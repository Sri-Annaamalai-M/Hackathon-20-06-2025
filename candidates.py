# main.py - Updated with proper route integration
from fastapi import FastAPI, HTTPException, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import logging
from typing import List
import uuid

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="AI Role Matcher API",
    description="AI-Powered Role Matching & Offer Recommendation Engine",
    version="1.0.0",
)

# CORS configuration - FIXED
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

# Try to import and use the actual routes, fall back to mock if they fail
try:
    from app.api.routes import candidates, roles, matches, offers
    from app.core.config import settings
    from app.db.mongodb import connect_to_mongo, close_mongo_connection
    
    # Database event handlers
    @app.on_event("startup")
    async def startup_db_client():
        try:
            await connect_to_mongo()
            logger.info("Connected to MongoDB successfully")
        except Exception as e:
            logger.warning(f"Failed to connect to MongoDB: {e}")
    
    @app.on_event("shutdown")
    async def shutdown_db_client():
        try:
            await close_mongo_connection()
        except Exception as e:
            logger.warning(f"Error closing MongoDB connection: {e}")
    
    # Include the actual API routes
    app.include_router(candidates.router, prefix="/api", tags=["candidates"])
    app.include_router(roles.router, prefix="/api", tags=["roles"])
    app.include_router(matches.router, prefix="/api", tags=["matches"])
    app.include_router(offers.router, prefix="/api", tags=["offers"])
    
    logger.info("Using actual API routes with database")
    USING_REAL_ROUTES = True
    
except ImportError as e:
    logger.warning(f"Failed to import actual routes: {e}")
    logger.info("Falling back to mock endpoints")
    USING_REAL_ROUTES = False

# Fallback mock endpoints (only used if real routes fail to import)
if not USING_REAL_ROUTES:
    # In-memory storage for demo
    candidates_db = [
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
                    "email": f"candidate{len(candidates_db) + len(processed_candidates) + 1}@example.com",
                    "skills": ["JavaScript", "Python", "React"],
                    "experience": "2-5 years",
                    "location": "Remote",
                    "education": "Bachelor's Degree",
                    "source_file": file.filename,
                    "file_size": file_size,
                    "processed_at": datetime.now().isoformat(),
                    "created_at": datetime.now().isoformat()
                }
                
                candidates_db.append(mock_candidate)
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
                "total_candidates": len(candidates_db),
                "processing_time": "2.5 seconds",
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
            logger.info(f"Returning {len(candidates_db)} candidates")
            return candidates_db
        except Exception as e:
            logger.error(f"Error in get_candidates: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))
    
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
    
    @app.get("/api/matches/")
    async def get_matches():
        try:
            matches = []
            for i, candidate in enumerate(candidates_db[:2]):
                match_id = f"match{i+1}"
                role_id = f"role{(i % 2) + 1}"
                
                matches.append({
                    "_id": match_id,
                    "candidate_id": candidate["_id"],
                    "role_id": role_id,
                    "match_score": 85 + (i * 7),
                    "status": "Matched",
                    "created_at": datetime.now().isoformat()
                })
            
            return matches
        except Exception as e:
            logger.error(f"Error in get_matches: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))
    
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

# Health check endpoints
@app.get("/health")
async def health_check():
    return {
        "status": "healthy", 
        "timestamp": datetime.now().isoformat(),
        "service": "AI Role Matcher Backend",
        "using_real_routes": USING_REAL_ROUTES
    }

@app.get("/api/health")
async def api_health_check():
    return {
        "status": "api_healthy", 
        "timestamp": datetime.now().isoformat(),
        "routes": "real" if USING_REAL_ROUTES else "mock"
    }

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "Welcome to the AI Role Matcher API",
        "version": "1.0.0",
        "status": "running",
        "routes": "real" if USING_REAL_ROUTES else "mock",
        "endpoints": {
            "health": "/health",
            "candidates": "/api/candidates/",
            "upload": "/api/candidates/upload",
            "roles": "/api/roles/",
            "matches": "/api/matches/",
            "offers": "/api/offers/"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)