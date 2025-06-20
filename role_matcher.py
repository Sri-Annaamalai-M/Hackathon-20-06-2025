# app/agents/role_matcher.py
import logging
import json
from typing import List, Dict, Any
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import ChatPromptTemplate
from langchain.chains import LLMChain
from sentence_transformers import SentenceTransformer
from bson import ObjectId
from datetime import datetime

from app.core.config import settings
from app.db.mongodb import get_candidate_collection, get_role_collection, get_match_collection
from app.db.vector_store import MongoDBVectorStore  # Using MongoDB instead of Pinecone

logger = logging.getLogger(__name__)

class RoleMatchingAgent:
    """Agent to match candidates with open roles using RAG."""
    
    def __init__(self):
        # Initialize Gemini model
        self.llm = ChatGoogleGenerativeAI(
            model="learnlm-2.0-flash-experimental",
            temperature=0.2,
            google_api_key=settings.GOOGLE_API_KEY
        )
        
        # Use SentenceTransformer for embeddings
        self.sentence_model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Set up matching prompt
        self.match_prompt = ChatPromptTemplate.from_template(
            """You are an expert HR system designed to match candidates with job roles optimally.
            
            # Candidate Profile:
            {candidate_profile}
            
            # Job Role:
            {role_profile}
            
            # Similar Role Benchmarks:
            {role_benchmarks}
            
            # Skill Mapping Context:
            {skill_mapping}
            
            Task: Analyze how well this candidate matches the role based on:
            1. Skill alignment (exact and semantic matching)
            2. Experience relevance
            3. Education/certification fit
            4. Candidate preferences match
            
            Provide:
            1. A match score (0-100)
            2. A list of matched skills
            3. A list of missing required skills
            4. A detailed explanation of the match quality
            
            Format your response as a valid JSON object with fields:
            - match_score (integer)
            - skill_match (object with "matched" and "missing" arrays)
            - explanation (string)
            """
        )
        
        self.matcher_chain = LLMChain(
            llm=self.llm,
            prompt=self.match_prompt
        )
    
    async def match_candidates_to_roles(self, candidate_ids=None, role_ids=None):
        """Match specified candidates to specified roles, or all if not specified."""
        try:
            # Get candidates
            candidate_collection = get_candidate_collection()
            role_collection = get_role_collection()
            
            # Apply filters if provided
            candidate_filter = {"_id": {"$in": [ObjectId(cid) for cid in candidate_ids]}} if candidate_ids else {}
            role_filter = {"_id": {"$in": [ObjectId(rid) for rid in role_ids]}} if role_ids else {}
            
            # Add active filter for roles
            role_filter["is_active"] = True
            
            # Fetch candidates and roles
            candidates = await candidate_collection.find(candidate_filter).to_list(1000)
            roles = await role_collection.find(role_filter).to_list(100)
            
            logger.info(f"Matching {len(candidates)} candidates to {len(roles)} roles")
            
            results = []
            
            # Process each candidate against each role
            for candidate in candidates:
                for role in roles:
                    # Check blacklist conditions first
                    if self.should_blacklist(candidate, role):
                        logger.info(f"Skipping candidate {candidate['name']} for role {role['title']} due to blacklist conditions")
                        continue
                    
                    # Perform the match
                    match_result = await self.match_candidate_to_role(candidate, role)
                    
                    if match_result:
                        results.append(match_result)
            
            return results
        
        except Exception as e:
            logger.error(f"Error in role matching process: {str(e)}")
            return []
    
    def should_blacklist(self, candidate: Dict[str, Any], role: Dict[str, Any]) -> bool:
        """Check if a candidate should be blacklisted from a role."""
        # Implement blacklist logic here
        # Examples of blacklist conditions:
        
        # 1. Missing critical required experience
        if role.get("experience_required") and candidate.get("experience"):
            # Parse experience (simplified example)
            try:
                required_years = int(role["experience_required"].split("+")[0].strip())
                candidate_years = int(candidate["experience"].split()[0].strip())
                
                if candidate_years < required_years:
                    return True
            except (ValueError, IndexError):
                # If we can't parse, be conservative and don't blacklist
                pass
        
        # 2. Location conflict (if remote is not an option)
        if (role.get("location") != candidate.get("location") and 
            role.get("remote_option", "").lower() == "no" and
            candidate.get("remote_preference", "").lower() == "remote only"):
            return True
        
        # 3. Add more blacklist conditions as needed
        
        return False
    
    async def match_candidate_to_role(self, candidate: Dict[str, Any], role: Dict[str, Any]):
        """Match a specific candidate to a specific role."""
        try:
            # Format candidate profile as text
            candidate_profile = self.format_candidate_profile(candidate)
            
            # Format role profile as text
            role_profile = self.format_role_profile(role)
            
            # Get role benchmarks using MongoDB
            role_benchmarks = await self.retrieve_role_benchmarks(role)
            
            # Get skill mappings using MongoDB
            skill_mapping = await self.retrieve_skill_mappings(role, candidate)
            
            # Run the matching chain
            response = await self.matcher_chain.arun(
                candidate_profile=candidate_profile,
                role_profile=role_profile,
                role_benchmarks=role_benchmarks,
                skill_mapping=skill_mapping
            )
            
            # Parse the response
            match_data = json.loads(response)
            
            # Create match record
            match_record = {
                "candidate_id": candidate["_id"],
                "role_id": role["_id"],
                "match_score": match_data["match_score"],
                "skill_match": match_data["skill_match"],
                "explanation": match_data["explanation"],
                "status": "Matched" if match_data["match_score"] >= 70 else "Review Needed"
            }
            
            # Store the match in the database
            await self.store_match(match_record)
            
            return match_record
        
        except Exception as e:
            logger.error(f"Error matching candidate {candidate.get('name', 'Unknown')} to role {role.get('title', 'Unknown')}: {str(e)}")
            return None
    
    def format_candidate_profile(self, candidate: Dict[str, Any]) -> str:
        """Format candidate profile as text for the LLM."""
        return f"""
        Name: {candidate.get('name', 'Unknown')}
        Email: {candidate.get('email', 'Unknown')}
        Skills: {', '.join(candidate.get('skills', []))}
        Experience: {candidate.get('experience', 'Not specified')}
        Education: {candidate.get('education', 'Not specified')}
        Certifications: {', '.join(candidate.get('certifications', []) or [])}
        Current CTC: {candidate.get('current_ctc', 'Not specified')}
        Expected CTC: {candidate.get('expected_ctc', 'Not specified')}
        Notice Period: {candidate.get('notice_period', 'Not specified')}
        Location: {candidate.get('location', 'Not specified')}
        Remote Preference: {candidate.get('remote_preference', 'Not specified')}
        Interview Scores: {json.dumps(candidate.get('interview_scores', {})) if candidate.get('interview_scores') else 'Not available'}
        Interview Feedback: {candidate.get('interview_feedback', 'Not available')}
        Preferences: {json.dumps(candidate.get('preferences', {})) if candidate.get('preferences') else 'Not specified'}
        """
    
    def format_role_profile(self, role: Dict[str, Any]) -> str:
        """Format role profile as text for the LLM."""
        return f"""
        Title: {role.get('title', 'Unknown')}
        Department: {role.get('department', 'Unknown')}
        Description: {role.get('description', 'Not specified')}
        Required Skills: {', '.join(role.get('required_skills', []))}
        Preferred Skills: {', '.join(role.get('preferred_skills', []) or [])}
        Experience Required: {role.get('experience_required', 'Not specified')}
        Education Required: {role.get('education_required', 'Not specified')}
        Certifications Required: {', '.join(role.get('certifications_required', []) or [])}
        Salary Range: {json.dumps(role.get('salary_range', {})) if role.get('salary_range') else 'Not specified'}
        Location: {role.get('location', 'Not specified')}
        Remote Option: {role.get('remote_option', 'Not specified')}
        Team Size: {role.get('team_size', 'Not specified')}
        Hiring Manager: {role.get('hiring_manager', 'Not specified')}
        """
    
    async def retrieve_role_benchmarks(self, role: Dict[str, Any]) -> str:
        """Retrieve similar role benchmarks using MongoDB."""
        try:
            # Create a query from the role
            query = f"{role.get('title', '')} {role.get('department', '')} {' '.join(role.get('required_skills', []))}"
            
            # Get embedding for the query
            query_embedding = self.sentence_model.encode(query).tolist()
            
            # Query MongoDB for similar roles
            results = await MongoDBVectorStore.query_embeddings(
                query_vector=query_embedding,
                top_k=3,
                filter_type="role_benchmark"
            )
            
            if not results or not results.get("matches"):
                return "No similar role benchmarks found."
            
            # Format the results
            benchmarks = []
            for match in results.get("matches", []):
                metadata = match.get("metadata", {})
                benchmarks.append(f"""
                Similar Role: {metadata.get('title', 'Unknown')}
                Typical Experience: {metadata.get('typical_experience', 'Not specified')}
                Key Skills: {', '.join(metadata.get('key_skills', []))}
                Typical Salary Range: {metadata.get('salary_range', 'Not specified')}
                """)
            
            return "\n".join(benchmarks)
        
        except Exception as e:
            logger.error(f"Error retrieving role benchmarks: {str(e)}")
            return "Error retrieving role benchmarks."
    
    async def retrieve_skill_mappings(self, role: Dict[str, Any], candidate: Dict[str, Any]) -> str:
        """Retrieve semantic skill mappings using MongoDB."""
        try:
            # Combine skills from role and candidate
            all_skills = list(set(
                role.get('required_skills', []) + 
                role.get('preferred_skills', []) + 
                candidate.get('skills', [])
            ))
            
            if not all_skills:
                return "No skills to map."
            
            # Create a query from the skills
            query = f"skill mappings for {' '.join(all_skills)}"
            
            # Get embedding for the query
            query_embedding = self.sentence_model.encode(query).tolist()
            
            # Query MongoDB for skill mappings
            results = await MongoDBVectorStore.query_embeddings(
                query_vector=query_embedding,
                top_k=5,
                filter_type="skill_mapping"
            )
            
            if not results or not results.get("matches"):
                return "No skill mappings found."
            
            # Format the results
            mappings = []
            for match in results.get("matches", []):
                metadata = match.get("metadata", {})
                mappings.append(f"""
                Skill: {metadata.get('skill', 'Unknown')}
                Similar Skills: {', '.join(metadata.get('similar_skills', []))}
                Category: {metadata.get('category', 'Not specified')}
                """)
            
            return "\n".join(mappings)
        
        except Exception as e:
            logger.error(f"Error retrieving skill mappings: {str(e)}")
            return "Error retrieving skill mappings."
    
    async def store_match(self, match_record: Dict[str, Any]):
        """Store the match result in the database."""
        try:
            match_collection = get_match_collection()
            
            # Check if match already exists
            existing_match = await match_collection.find_one({
                "candidate_id": match_record["candidate_id"],
                "role_id": match_record["role_id"]
            })
            
            if existing_match:
                # Update existing match
                await match_collection.update_one(
                    {"_id": existing_match["_id"]},
                    {"$set": {
                        "match_score": match_record["match_score"],
                        "skill_match": match_record["skill_match"],
                        "explanation": match_record["explanation"],
                        "status": match_record["status"],
                        "updated_at": datetime.utcnow()
                    }}
                )
                logger.info(f"Updated existing match: {existing_match['_id']}")
            else:
                # Insert new match
                match_record["created_at"] = datetime.utcnow()
                match_record["updated_at"] = datetime.utcnow()
                
                result = await match_collection.insert_one(match_record)
                logger.info(f"Inserted new match with ID: {result.inserted_id}")
        
        except Exception as e:
            logger.error(f"Error storing match record: {str(e)}")