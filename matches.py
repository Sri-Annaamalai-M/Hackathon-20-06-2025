# app/api/routes/matches.py
from typing import List, Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks, Query
from bson import ObjectId
from datetime import datetime

from app.db.mongodb import get_match_collection, get_candidate_collection, get_role_collection
from app.schemas.models import MatchResponse, MatchUpdate, MatchWithDetails
from app.agents.role_matcher import RoleMatchingAgent
from app.agents.explanation_generator import ExplanationGeneratorAgent

router = APIRouter()

# Helper function to validate ObjectId
def validate_object_id(id: str):
    if not ObjectId.is_valid(id):
        raise HTTPException(status_code=400, detail=f"Invalid id format {id}")
    return id

@router.post("/matches/process", status_code=202)
async def process_matches(
    background_tasks: BackgroundTasks,
    candidate_ids: Optional[List[str]] = Query(None),
    role_ids: Optional[List[str]] = Query(None)
):
    """Process matches for selected candidates and roles, or all if not specified."""
    # Validate object IDs if provided
    if candidate_ids:
        candidate_ids = [validate_object_id(id) for id in candidate_ids]
    if role_ids:
        role_ids = [validate_object_id(id) for id in role_ids]
    
    # Create matching agent
    matcher = RoleMatchingAgent()
    
    # Add background task for matching
    background_tasks.add_task(matcher.match_candidates_to_roles, candidate_ids, role_ids)
    
    return {"message": "Match processing started", "candidates": len(candidate_ids) if candidate_ids else "all", "roles": len(role_ids) if role_ids else "all"}

@router.get("/matches/", response_model=List[MatchResponse])
async def get_matches(
    candidate_id: Optional[str] = None,
    role_id: Optional[str] = None,
    min_score: Optional[float] = None,
    status: Optional[str] = None
):
    """Get all matches with optional filtering."""
    match_collection = get_match_collection()
    
    # Build filter
    filter_query = {}
    
    if candidate_id:
        validate_object_id(candidate_id)
        filter_query["candidate_id"] = ObjectId(candidate_id)
    
    if role_id:
        validate_object_id(role_id)
        filter_query["role_id"] = ObjectId(role_id)
    
    if min_score is not None:
        filter_query["match_score"] = {"$gte": min_score}
    
    if status:
        filter_query["status"] = status
    
    matches = await match_collection.find(filter_query).to_list(1000)
    return matches

@router.get("/matches/{match_id}", response_model=MatchWithDetails)
async def get_match(match_id: str):
    """Get a specific match by ID with candidate and role details."""
    validate_object_id(match_id)
    match_collection = get_match_collection()
    candidate_collection = get_candidate_collection()
    role_collection = get_role_collection()
    
    match = await match_collection.find_one({"_id": ObjectId(match_id)})
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")
    
    # Get candidate and role details
    candidate = await candidate_collection.find_one({"_id": match["candidate_id"]})
    role = await role_collection.find_one({"_id": match["role_id"]})
    
    if not candidate or not role:
        raise HTTPException(status_code=404, detail="Candidate or role not found")
    
    # Combine data
    match_with_details = {**match, "candidate": candidate, "role": role}
    
    return match_with_details

@router.put("/matches/{match_id}", response_model=MatchResponse)
async def update_match(match_id: str, match_update: MatchUpdate):
    """Update a match."""
    validate_object_id(match_id)
    match_collection = get_match_collection()
    
    # Check if match exists
    match = await match_collection.find_one({"_id": ObjectId(match_id)})
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")
    
    # Update match
    update_data = match_update.dict(exclude_unset=True)
    update_data["updated_at"] = datetime.utcnow()
    
    await match_collection.update_one(
        {"_id": ObjectId(match_id)},
        {"$set": update_data}
    )
    
    # Return updated match
    updated_match = await match_collection.find_one({"_id": ObjectId(match_id)})
    return updated_match

@router.post("/matches/{match_id}/regenerate-explanation", response_model=MatchResponse)
async def regenerate_explanation(match_id: str):
    """Regenerate explanation for a match."""
    validate_object_id(match_id)
    match_collection = get_match_collection()
    
    # Check if match exists
    match = await match_collection.find_one({"_id": ObjectId(match_id)})
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")
    
    # Create explanation generator agent
    explanation_generator = ExplanationGeneratorAgent()
    
    # Generate new explanation
    explanation = await explanation_generator.generate_match_explanation(match_id)
    
    # Return updated match
    updated_match = await match_collection.find_one({"_id": ObjectId(match_id)})
    return updated_match

@router.post("/matches/batch-explain", status_code=202)
async def batch_regenerate_explanations(background_tasks: BackgroundTasks):
    """Regenerate explanations for all matches in the background."""
    explanation_generator = ExplanationGeneratorAgent()
    background_tasks.add_task(explanation_generator.batch_generate_explanations, "match")
    
    return {"message": "Batch explanation regeneration started"}

@router.delete("/matches/{match_id}", status_code=204)
async def delete_match(match_id: str):
    """Delete a match."""
    validate_object_id(match_id)
    match_collection = get_match_collection()
    
    # Check if match exists
    match = await match_collection.find_one({"_id": ObjectId(match_id)})
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")
    
    # Delete match
    await match_collection.delete_one({"_id": ObjectId(match_id)})
    
    return None