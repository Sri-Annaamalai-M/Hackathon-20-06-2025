# app/api/routes/offers.py
from typing import List, Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks, Query
from bson import ObjectId
from datetime import datetime

from app.db.mongodb import get_offer_collection, get_candidate_collection, get_role_collection, get_match_collection, get_feedback_collection
from app.schemas.models import OfferResponse, OfferUpdate, OfferWithDetails, FeedbackCreate, FeedbackResponse
from app.agents.offer_recommender import OfferRecommendationAgent
from app.agents.explanation_generator import ExplanationGeneratorAgent
from app.agents.feedback_processor import FeedbackProcessorAgent

router = APIRouter()

# Helper function to validate ObjectId
def validate_object_id(id: str):
    if not ObjectId.is_valid(id):
        raise HTTPException(status_code=400, detail=f"Invalid id format {id}")
    return id

@router.post("/offers/generate", status_code=202)
async def generate_offers(
    background_tasks: BackgroundTasks,
    match_ids: Optional[List[str]] = Query(None)
):
    """Generate offer recommendations for specified matches, or all pending matches if not specified."""
    # Validate object IDs if provided
    if match_ids:
        match_ids = [validate_object_id(id) for id in match_ids]
    
    # Create offer recommendation agent
    offer_recommender = OfferRecommendationAgent()
    
    # Add background task for offer generation
    background_tasks.add_task(offer_recommender.generate_offers, match_ids)
    
    return {"message": "Offer generation started", "matches": len(match_ids) if match_ids else "all pending matches"}

@router.get("/offers/", response_model=List[OfferResponse])
async def get_offers(
    candidate_id: Optional[str] = None,
    role_id: Optional[str] = None,
    status: Optional[str] = None
):
    """Get all offers with optional filtering."""
    offer_collection = get_offer_collection()
    
    # Build filter
    filter_query = {}
    
    if candidate_id:
        validate_object_id(candidate_id)
        filter_query["candidate_id"] = ObjectId(candidate_id)
    
    if role_id:
        validate_object_id(role_id)
        filter_query["role_id"] = ObjectId(role_id)
    
    if status:
        filter_query["status"] = status
    
    offers = await offer_collection.find(filter_query).to_list(1000)
    return offers

@router.get("/offers/{offer_id}", response_model=OfferWithDetails)
async def get_offer(offer_id: str):
    """Get a specific offer by ID with candidate and role details."""
    validate_object_id(offer_id)
    offer_collection = get_offer_collection()
    candidate_collection = get_candidate_collection()
    role_collection = get_role_collection()
    
    offer = await offer_collection.find_one({"_id": ObjectId(offer_id)})
    if not offer:
        raise HTTPException(status_code=404, detail="Offer not found")
    
    # Get candidate and role details
    candidate = await candidate_collection.find_one({"_id": offer["candidate_id"]})
    role = await role_collection.find_one({"_id": offer["role_id"]})
    
    if not candidate or not role:
        raise HTTPException(status_code=404, detail="Candidate or role not found")
    
    # Combine data
    offer_with_details = {**offer, "candidate": candidate, "role": role}
    
    return offer_with_details

@router.put("/offers/{offer_id}", response_model=OfferResponse)
async def update_offer(offer_id: str, offer_update: OfferUpdate):
    """Update an offer."""
    validate_object_id(offer_id)
    offer_collection = get_offer_collection()
    
    # Check if offer exists
    offer = await offer_collection.find_one({"_id": ObjectId(offer_id)})
    if not offer:
        raise HTTPException(status_code=404, detail="Offer not found")
    
    # Update offer
    update_data = offer_update.dict(exclude_unset=True)
    update_data["updated_at"] = datetime.utcnow()
    
    # If status is changed to "Modified", update the status
    if update_data.get("status") == "Modified" or (
        "offer" in update_data and offer["status"] == "Pending Approval"
    ):
        update_data["status"] = "Modified"
    
    await offer_collection.update_one(
        {"_id": ObjectId(offer_id)},
        {"$set": update_data}
    )
    
    # Return updated offer
    updated_offer = await offer_collection.find_one({"_id": ObjectId(offer_id)})
    return updated_offer

@router.post("/offers/{offer_id}/approve", response_model=OfferResponse)
async def approve_offer(offer_id: str):
    """Approve an offer."""
    validate_object_id(offer_id)
    offer_collection = get_offer_collection()
    feedback_collection = get_feedback_collection()
    
    # Check if offer exists
    offer = await offer_collection.find_one({"_id": ObjectId(offer_id)})
    if not offer:
        raise HTTPException(status_code=404, detail="Offer not found")
    
    # Update offer status
    await offer_collection.update_one(
        {"_id": ObjectId(offer_id)},
        {"$set": {"status": "Approved", "updated_at": datetime.utcnow()}}
    )
    
    # Create feedback record for approval
    feedback = {
        "entity_type": "offer",
        "entity_id": ObjectId(offer_id),
        "feedback_type": "approval",
        "comments": "Offer approved by HR",
        "created_at": datetime.utcnow()
    }
    
    await feedback_collection.insert_one(feedback)
    
    # Process the feedback in the background
    feedback_processor = FeedbackProcessorAgent()
    await feedback_processor.process_feedback(str(feedback["_id"]))
    
    # Return updated offer
    updated_offer = await offer_collection.find_one({"_id": ObjectId(offer_id)})
    return updated_offer

@router.post("/offers/{offer_id}/reject", response_model=OfferResponse)
async def reject_offer(offer_id: str, comments: str = ""):
    """Reject an offer."""
    validate_object_id(offer_id)
    offer_collection = get_offer_collection()
    feedback_collection = get_feedback_collection()
    
    # Check if offer exists
    offer = await offer_collection.find_one({"_id": ObjectId(offer_id)})
    if not offer:
        raise HTTPException(status_code=404, detail="Offer not found")
    
    # Update offer status
    await offer_collection.update_one(
        {"_id": ObjectId(offer_id)},
        {"$set": {"status": "Rejected", "updated_at": datetime.utcnow()}}
    )
    
    # Create feedback record for rejection
    feedback = {
        "entity_type": "offer",
        "entity_id": ObjectId(offer_id),
        "feedback_type": "rejection",
        "comments": comments or "Offer rejected by HR",
        "created_at": datetime.utcnow()
    }
    
    await feedback_collection.insert_one(feedback)
    
    # Process the feedback in the background
    feedback_processor = FeedbackProcessorAgent()
    await feedback_processor.process_feedback(str(feedback["_id"]))
    
    # Return updated offer
    updated_offer = await offer_collection.find_one({"_id": ObjectId(offer_id)})
    return updated_offer

@router.post("/offers/{offer_id}/regenerate-explanation", response_model=OfferResponse)
async def regenerate_explanation(offer_id: str):
    """Regenerate explanation for an offer."""
    validate_object_id(offer_id)
    offer_collection = get_offer_collection()
    
    # Check if offer exists
    offer = await offer_collection.find_one({"_id": ObjectId(offer_id)})
    if not offer:
        raise HTTPException(status_code=404, detail="Offer not found")
    
    # Create explanation generator agent
    explanation_generator = ExplanationGeneratorAgent()
    
    # Generate new explanation
    explanation = await explanation_generator.generate_offer_explanation(offer_id)
    
    # Return updated offer
    updated_offer = await offer_collection.find_one({"_id": ObjectId(offer_id)})
    return updated_offer

@router.post("/offers/batch-explain", status_code=202)
async def batch_regenerate_explanations(background_tasks: BackgroundTasks):
    """Regenerate explanations for all offers in the background."""
    explanation_generator = ExplanationGeneratorAgent()
    background_tasks.add_task(explanation_generator.batch_generate_explanations, "offer")
    
    return {"message": "Batch explanation regeneration started"}

@router.post("/offers/feedback", response_model=FeedbackResponse)
async def submit_feedback(feedback: FeedbackCreate, background_tasks: BackgroundTasks):
    """Submit feedback for an offer or match."""
    # Validate entity ID
    validate_object_id(str(feedback.entity_id))
    
    # Validate entity type
    if feedback.entity_type not in ["match", "offer"]:
        raise HTTPException(status_code=400, detail="Invalid entity type. Must be 'match' or 'offer'")
    
    # Validate feedback type
    if feedback.feedback_type not in ["approval", "rejection", "modification"]:
        raise HTTPException(status_code=400, detail="Invalid feedback type. Must be 'approval', 'rejection', or 'modification'")
    
    # Insert feedback
    feedback_collection = get_feedback_collection()
    
    feedback_dict = feedback.dict()
    feedback_dict["created_at"] = datetime.utcnow()
    
    result = await feedback_collection.insert_one(feedback_dict)
    
    # Process feedback in background
    feedback_processor = FeedbackProcessorAgent()
    background_tasks.add_task(feedback_processor.process_feedback, str(result.inserted_id))
    
    # Return the created feedback
    created_feedback = await feedback_collection.find_one({"_id": result.inserted_id})
    return created_feedback

@router.delete("/offers/{offer_id}", status_code=204)
async def delete_offer(offer_id: str):
    """Delete an offer."""
    validate_object_id(offer_id)
    offer_collection = get_offer_collection()
    
    # Check if offer exists
    offer = await offer_collection.find_one({"_id": ObjectId(offer_id)})
    if not offer:
        raise HTTPException(status_code=404, detail="Offer not found")
    
    # Delete offer
    await offer_collection.delete_one({"_id": ObjectId(offer_id)})
    
    return None