# main.py - Complete version with all endpoints
from fastapi import FastAPI, HTTPException, File, UploadFile, Query
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import logging
from typing import List, Optional
import uuid
import asyncio

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="AI Role Matcher API",
    description="AI-Powered Role Matching & Offer Recommendation Engine",
    version="1.0.0",
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Health check endpoints
@app.get("/health")
async def health_check():
    return {
        "status": "healthy", 
        "timestamp": datetime.now().isoformat(),
        "service": "AI Role Matcher Backend"
    }

@app.get("/api/health")
async def api_health_check():
    return {
        "status": "api_healthy", 
        "timestamp": datetime.now().isoformat()
    }

# Candidate endpoints
@app.post("/api/candidates/upload")
async def upload_candidate_files(files: List[UploadFile] = File(...)):
    try:
        uploaded_files = []
        processed_candidates = []
        
        for file in files:
            # Validate file type
            if not file.filename.lower().endswith(('.pdf', '.docx')):
                raise HTTPException(
                    status_code=400, 
                    detail=f"Invalid file type for {file.filename}. Only PDF and DOCX files are supported."
                )
            
            # Read file content
            content = await file.read()
            file_size = len(content)
            
            logger.info(f"Processing file: {file.filename} ({file_size} bytes)")
            
            # Create mock candidate based on filename
            candidate_id = str(uuid.uuid4())
            mock_candidate = {
                "_id": candidate_id,
                "name": f"Candidate from {file.filename}",
                "email": f"candidate{len(processed_candidates) + 1}@example.com",
                "skills": ["JavaScript", "Python", "React"],
                "experience": "2-5 years",
                "location": "Remote",
                "education": "Bachelor's Degree",
                "source_file": file.filename,
                "file_size": file_size,
                "processed_at": datetime.now().isoformat(),
                "created_at": datetime.now().isoformat()
            }
            
            processed_candidates.append(mock_candidate)
            
            uploaded_files.append({
                "filename": file.filename,
                "size": file_size,
                "content_type": file.content_type,
                "candidate_id": candidate_id
            })
        
        logger.info(f"Successfully processed {len(files)} files, created {len(processed_candidates)} candidates")
        
        return {
            "message": f"Successfully uploaded and processed {len(files)} files",
            "uploaded_files": uploaded_files,
            "processed_candidates": len(processed_candidates),
            "status": "completed"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading files: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing files: {str(e)}")

@app.get("/api/candidates/")
async def get_candidates():
    try:
        return [
            {
                "_id": "candidate1",
                "name": "John Doe",
                "email": "john@example.com",
                "skills": ["React", "Node.js", "TypeScript"],
                "experience": "3 years",
                "location": "New York",
                "created_at": datetime.now().isoformat()
            },
            {
                "_id": "candidate2",
                "name": "Jane Smith", 
                "email": "jane@example.com",
                "skills": ["Python", "FastAPI", "Machine Learning"],
                "experience": "5 years",
                "location": "San Francisco",
                "created_at": datetime.now().isoformat()
            }
        ]
    except Exception as e:
        logger.error(f"Error in get_candidates: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Role endpoints
@app.get("/api/roles/")
async def get_roles(active_only: bool = True):
    try:
        roles = [
            {
                "_id": "role1",
                "title": "Frontend Developer",
                "department": "Engineering",
                "required_skills": ["React", "JavaScript", "CSS"],
                "preferred_skills": ["TypeScript", "Node.js"],
                "experience_required": "2+ years",
                "location": "New York",
                "is_active": True,
                "created_at": datetime.now().isoformat()
            },
            {
                "_id": "role2",
                "title": "Backend Developer",
                "department": "Engineering", 
                "required_skills": ["Python", "FastAPI", "PostgreSQL"],
                "preferred_skills": ["Docker", "AWS"],
                "experience_required": "3+ years",
                "location": "Remote",
                "is_active": True,
                "created_at": datetime.now().isoformat()
            },
            {
                "_id": "role3",
                "title": "Data Scientist",
                "department": "Analytics",
                "required_skills": ["Python", "Machine Learning", "TensorFlow"],
                "preferred_skills": ["PyTorch", "SQL"],
                "experience_required": "4+ years",
                "location": "San Francisco",
                "is_active": False,
                "created_at": datetime.now().isoformat()
            }
        ]
        
        if active_only:
            roles = [role for role in roles if role.get("is_active", True)]
        
        logger.info(f"Returning {len(roles)} roles (active_only={active_only})")
        return roles
        
    except Exception as e:
        logger.error(f"Error in get_roles: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Match endpoints
@app.get("/api/matches/")
async def get_matches():
    try:
        return [
            {
                "_id": "match1",
                "candidate_id": "candidate1",
                "role_id": "role1", 
                "match_score": 85,
                "status": "Matched",
                "created_at": datetime.now().isoformat()
            },
            {
                "_id": "match2",
                "candidate_id": "candidate2",
                "role_id": "role2",
                "match_score": 92,
                "status": "Matched", 
                "created_at": datetime.now().isoformat()
            }
        ]
    except Exception as e:
        logger.error(f"Error in get_matches: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/matches/process")
async def process_matches(
    candidate_ids: Optional[List[str]] = Query(None),
    role_ids: Optional[List[str]] = Query(None)
):
    """Process matches for selected candidates and roles, or all if not specified."""
    try:
        logger.info(f"Starting match processing for candidates: {candidate_ids}, roles: {role_ids}")
        
        # Simulate processing time
        await asyncio.sleep(2)
        
        # Create some mock matches
        new_matches = []
        candidate_count = len(candidate_ids) if candidate_ids else 2
        role_count = len(role_ids) if role_ids else 2
        
        for i in range(min(candidate_count, role_count)):
            match_id = f"match_new_{i+1}"
            new_match = {
                "_id": match_id,
                "candidate_id": candidate_ids[i] if candidate_ids else f"candidate{i+1}",
                "role_id": role_ids[i] if role_ids else f"role{i+1}",
                "match_score": 75 + (i * 10),
                "status": "Matched",
                "explanation": f"AI-generated match with {75 + (i * 10)}% compatibility",
                "skill_match": {
                    "matched": ["Python", "JavaScript"],
                    "missing": ["AWS", "Docker"]
                },
                "created_at": datetime.now().isoformat()
            }
            new_matches.append(new_match)
        
        logger.info(f"Generated {len(new_matches)} new matches")
        
        return {
            "message": "Match processing completed successfully",
            "matches_created": len(new_matches),
            "processing_time": "2.0 seconds",
            "status": "completed"
        }
        
    except Exception as e:
        logger.error(f"Error processing matches: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing matches: {str(e)}")

@app.get("/api/matches/{match_id}")
async def get_match(match_id: str):
    """Get a specific match by ID with candidate and role details."""
    try:
        # Mock detailed match data
        mock_match = {
            "_id": match_id,
            "candidate_id": "candidate1",
            "role_id": "role1",
            "match_score": 85,
            "status": "Matched",
            "explanation": "This candidate shows strong alignment with the role requirements. Their experience in React and Node.js directly matches the frontend developer position needs. The 3 years of experience meets the minimum requirement, and their location preference aligns with the role.",
            "skill_match": {
                "matched": ["React", "JavaScript", "Node.js"],
                "missing": ["TypeScript", "CSS"]
            },
            "candidate": {
                "_id": "candidate1",
                "name": "John Doe",
                "email": "john@example.com",
                "skills": ["React", "Node.js", "JavaScript", "Python"],
                "experience": "3 years",
                "location": "New York",
                "education": "Bachelor's in Computer Science"
            },
            "role": {
                "_id": "role1",
                "title": "Frontend Developer",
                "department": "Engineering",
                "required_skills": ["React", "JavaScript", "CSS"],
                "preferred_skills": ["TypeScript", "Node.js"],
                "experience_required": "2+ years",
                "location": "New York"
            },
            "created_at": datetime.now().isoformat()
        }
        
        logger.info(f"Returning detailed match data for {match_id}")
        return mock_match
        
    except Exception as e:
        logger.error(f"Error fetching match {match_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Offer endpoints
@app.get("/api/offers/")
async def get_offers():
    try:
        return [
            {
                "_id": "offer1",
                "candidate_id": "candidate1",
                "role_id": "role1",
                "match_score": 85,
                "status": "Pending Approval",
                "offer": {
                    "base_salary": 100000,
                    "bonus": 10000,
                    "equity": "1%",
                    "total_ctc": 110000
                },
                "created_at": datetime.now().isoformat()
            },
            {
                "_id": "offer2",
                "candidate_id": "candidate2", 
                "role_id": "role2",
                "match_score": 92,
                "status": "Approved",
                "offer": {
                    "base_salary": 120000,
                    "bonus": 15000,
                    "equity": "2%", 
                    "total_ctc": 135000
                },
                "created_at": datetime.now().isoformat()
            }
        ]
    except Exception as e:
        logger.error(f"Error in get_offers: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/offers/generate")
async def generate_offers(match_ids: Optional[List[str]] = Query(None)):
    """Generate offer recommendations for specified matches."""
    try:
        logger.info(f"Starting offer generation for matches: {match_ids}")
        
        # Simulate processing time
        await asyncio.sleep(1.5)
        
        # Create mock offers
        new_offers = []
        match_count = len(match_ids) if match_ids else 1
        
        for i, match_id in enumerate(match_ids or ["match1"]):
            offer_id = f"offer_new_{i+1}"
            base_salary = 90000 + (i * 10000)
            
            new_offer = {
                "_id": offer_id,
                "match_id": match_id,
                "candidate_id": f"candidate{i+1}",
                "role_id": f"role{i+1}",
                "match_score": 85 + (i * 5),
                "status": "Pending Approval",
                "offer": {
                    "base_salary": base_salary,
                    "bonus": base_salary * 0.1,
                    "equity": f"{1 + i}%",
                    "total_ctc": base_salary * 1.15
                },
                "explanation": f"Competitive offer based on market analysis and candidate's {85 + (i * 5)}% match score",
                "created_at": datetime.now().isoformat()
            }
            new_offers.append(new_offer)
        
        logger.info(f"Generated {len(new_offers)} new offers")
        
        return {
            "message": "Offer generation completed successfully",
            "offers_created": len(new_offers),
            "processing_time": "1.5 seconds",
            "status": "completed"
        }
        
    except Exception as e:
        logger.error(f"Error generating offers: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating offers: {str(e)}")

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "Welcome to the AI Role Matcher API",
        "version": "1.0.0",
        "status": "running"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)