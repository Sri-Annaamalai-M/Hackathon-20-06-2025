# app/api/routes/roles.py
from typing import List
from fastapi import APIRouter, HTTPException, Depends
from bson import ObjectId
from datetime import datetime
from sentence_transformers import SentenceTransformer

from app.db.mongodb import get_role_collection
from app.schemas.models import RoleCreate, RoleResponse, RoleUpdate
from app.core.config import settings
from app.db.vector_store import MongoDBVectorStore

router = APIRouter()

# Initialize SentenceTransformer for embeddings
sentence_model = SentenceTransformer('all-MiniLM-L6-v2')

# Helper function to validate ObjectId
def validate_object_id(id: str):
    if not ObjectId.is_valid(id):
        raise HTTPException(status_code=400, detail=f"Invalid id format {id}")
    return id

@router.post("/roles/", response_model=RoleResponse)
async def create_role(role: RoleCreate):
    """Create a new role."""
    role_collection = get_role_collection()
    
    # Insert new role
    new_role = role.dict()
    new_role["created_at"] = datetime.utcnow()
    new_role["updated_at"] = datetime.utcnow()
    new_role["is_active"] = True
    
    result = await role_collection.insert_one(new_role)
    
    # Create embeddings for the role
    try:
        # Create role text for embedding
        role_text = f"""
        Title: {role.title}
        Department: {role.department}
        Description: {role.description or ''}
        Required Skills: {', '.join(role.required_skills)}
        Preferred Skills: {', '.join(role.preferred_skills or [])}
        Experience Required: {role.experience_required or ''}
        """
        
        # Generate embedding
        embedding = sentence_model.encode(role_text).tolist()
        
        # Store in MongoDB
        metadata = {
            "title": role.title,
            "department": role.department,
            "required_skills": role.required_skills,
            "preferred_skills": role.preferred_skills or [],
            "type": "role"
        }
        
        await MongoDBVectorStore.store_embedding(f"role_{result.inserted_id}", embedding, metadata)
    except Exception as e:
        # Log error but don't fail the request
        print(f"Error creating role embedding: {str(e)}")
    
    # Return the new role
    created_role = await role_collection.find_one({"_id": result.inserted_id})
    return created_role

@router.get("/roles/", response_model=List[RoleResponse])
async def get_roles(active_only: bool = True):
    """Get all roles."""
    role_collection = get_role_collection()
    
    # Filter for active roles if requested
    filter_query = {"is_active": True} if active_only else {}
    
    roles = await role_collection.find(filter_query).to_list(1000)
    return roles

@router.get("/roles/{role_id}", response_model=RoleResponse)
async def get_role(role_id: str):
    """Get a specific role by ID."""
    validate_object_id(role_id)
    role_collection = get_role_collection()
    
    role = await role_collection.find_one({"_id": ObjectId(role_id)})
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    
    return role

@router.put("/roles/{role_id}", response_model=RoleResponse)
async def update_role(role_id: str, role_update: RoleUpdate):
    """Update a role."""
    validate_object_id(role_id)
    role_collection = get_role_collection()
    
    # Check if role exists
    role = await role_collection.find_one({"_id": ObjectId(role_id)})
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    
    # Update role
    update_data = role_update.dict(exclude_unset=True)
    update_data["updated_at"] = datetime.utcnow()
    
    await role_collection.update_one(
        {"_id": ObjectId(role_id)},
        {"$set": update_data}
    )
    
    # Update embeddings if title or skills changed
    if any(key in update_data for key in ["title", "department", "required_skills", "preferred_skills"]):
        try:
            # Get updated role data
            updated_role = await role_collection.find_one({"_id": ObjectId(role_id)})
            
            # Create role text for embedding
            role_text = f"""
            Title: {updated_role['title']}
            Department: {updated_role['department']}
            Description: {updated_role.get('description', '')}
            Required Skills: {', '.join(updated_role['required_skills'])}
            Preferred Skills: {', '.join(updated_role.get('preferred_skills', []) or [])}
            Experience Required: {updated_role.get('experience_required', '')}
            """
            
            # Generate embedding
            embedding = sentence_model.encode(role_text).tolist()
            
            # Store in MongoDB
            metadata = {
                "title": updated_role['title'],
                "department": updated_role['department'],
                "required_skills": updated_role['required_skills'],
                "preferred_skills": updated_role.get('preferred_skills', []) or [],
                "type": "role"
            }
            
            await MongoDBVectorStore.store_embedding(f"role_{role_id}", embedding, metadata)
        except Exception as e:
            # Log error but don't fail the request
            print(f"Error updating role embedding: {str(e)}")
    
    # Return updated role
    updated_role = await role_collection.find_one({"_id": ObjectId(role_id)})
    return updated_role

@router.delete("/roles/{role_id}", status_code=204)
async def delete_role(role_id: str, soft_delete: bool = True):
    """Delete a role (soft delete by default)."""
    validate_object_id(role_id)
    role_collection = get_role_collection()
    
    # Check if role exists
    role = await role_collection.find_one({"_id": ObjectId(role_id)})
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    
    if soft_delete:
        # Soft delete - just mark as inactive
        await role_collection.update_one(
            {"_id": ObjectId(role_id)},
            {"$set": {"is_active": False, "updated_at": datetime.utcnow()}}
        )
    else:
        # Hard delete
        await role_collection.delete_one({"_id": ObjectId(role_id)})
        
        # Also delete from vector store
        try:
            await MongoDBVectorStore.delete_embedding(f"role_{role_id}")
        except Exception as e:
            print(f"Error deleting role embedding: {str(e)}")
    
    return None