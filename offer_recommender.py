# app/agents/offer_recommender.py
import logging
import json
from typing import List, Dict, Any
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import ChatPromptTemplate
from langchain.chains import LLMChain
from bson import ObjectId
from datetime import datetime, timedelta

from app.core.config import settings
from app.db.mongodb import get_candidate_collection, get_role_collection, get_match_collection, get_offer_collection

logger = logging.getLogger(__name__)

class OfferRecommendationAgent:
    """Agent to generate personalized offer packages based on matches."""
    
    def __init__(self):
        # Initialize Gemini model
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-pro",
            temperature=0.2,
            google_api_key=settings.GOOGLE_API_KEY
        )
        
        # Set up offer recommendation prompt
        self.offer_prompt = ChatPromptTemplate.from_template(
            """You are an expert HR compensation analyst responsible for generating fair and competitive offer packages.
            
            # Candidate Profile:
            {candidate_profile}
            
            # Job Role:
            {role_profile}
            
            # Match Information:
            Match Score: {match_score}
            Matched Skills: {matched_skills}
            Missing Skills: {missing_skills}
            
            # Market Data:
            {market_data}
            
            Task: Generate a personalized offer package based on:
            1. Skill-demand alignment (high-demand skills warrant higher CTC)
            2. Market benchmarks for the role, location, and experience
            3. Candidate preferences (remote vs on-site, etc.)
            4. Match quality and interview performance
            5. Current compensation (aim for 10-20% increase typically)
            
            Provide:
            1. Base salary
            2. Bonus (if applicable)
            3. Equity (if applicable)
            4. Benefits package
            5. Total CTC
            6. Start date recommendation
            7. Work arrangement (remote/hybrid/on-site)
            8. Detailed explanation of the offer rationale
            
            Format your response as a valid JSON object with fields:
            - offer (object with base_salary, bonus, equity, benefits array, total_ctc, start_date, remote)
            - explanation (string)
            """
        )
        
        self.offer_chain = LLMChain(
            llm=self.llm,
            prompt=self.offer_prompt
        )
        
        # Market data prompt
        self.market_data_prompt = ChatPromptTemplate.from_template(
            """You are an expert in compensation and salary benchmarks.
            Based on your knowledge, provide current market data for the following role:
            
            Role: {role_title}
            Department: {department}
            Location: {location}
            Experience Level: {experience}
            
            Include:
            1. Salary ranges (low, mid, high)
            2. Standard benefits
            3. Current demand for this role type
            4. Any relevant industry trends affecting compensation
            
            Format your response as market research data, not as recommendations.
            """
        )
        
        self.market_data_chain = LLMChain(
            llm=self.llm,
            prompt=self.market_data_prompt
        )
    
    async def generate_offers(self, match_ids=None):
        """Generate offer recommendations for specified matches, or all pending matches if not specified."""
        try:
            # Get collections
            match_collection = get_match_collection()
            candidate_collection = get_candidate_collection()
            role_collection = get_role_collection()
            
            # Apply filters if provided
            match_filter = {"_id": {"$in": [ObjectId(mid) for mid in match_ids]}} if match_ids else {}
            
            # Only process matches with good scores and proper status
            if not match_ids:
                match_filter["match_score"] = {"$gte": 70}
                match_filter["status"] = "Matched"
            
            # Fetch matches
            matches = await match_collection.find(match_filter).to_list(1000)
            
            logger.info(f"Generating offers for {len(matches)} matches")
            
            results = []
            
            # Process each match
            for match in matches:
                # Get candidate and role details
                candidate = await candidate_collection.find_one({"_id": match["candidate_id"]})
                role = await role_collection.find_one({"_id": match["role_id"]})
                
                if not candidate or not role:
                    logger.warning(f"Candidate or role not found for match {match['_id']}")
                    continue
                
                # Generate offer
                offer_result = await self.generate_offer(candidate, role, match)
                
                if offer_result:
                    results.append(offer_result)
            
            return results
        
        except Exception as e:
            logger.error(f"Error in offer generation process: {str(e)}")
            return []
    
    async def generate_offer(self, candidate: Dict[str, Any], role: Dict[str, Any], match: Dict[str, Any]):
        """Generate an offer for a specific match."""
        try:
            # Format candidate profile as text
            candidate_profile = self.format_candidate_profile(candidate)
            
            # Format role profile as text
            role_profile = self.format_role_profile(role)
            
            # Get matched and missing skills
            matched_skills = ", ".join(match.get("skill_match", {}).get("matched", []))
            missing_skills = ", ".join(match.get("skill_match", {}).get("missing", []))
            
            # Get market data
            market_data = await self.get_market_data(
                role.get("title", ""),
                role.get("department", ""),
                role.get("location", ""),
                candidate.get("experience", "")
            )
            
            # Run the offer chain
            response = await self.offer_chain.arun(
                candidate_profile=candidate_profile,
                role_profile=role_profile,
                match_score=match.get("match_score", 0),
                matched_skills=matched_skills,
                missing_skills=missing_skills,
                market_data=market_data
            )
            
            # Parse the response
            offer_data = json.loads(response)
            
            # Create offer record
            offer_record = {
                "candidate_id": candidate["_id"],
                "role_id": role["_id"],
                "match_id": match["_id"],
                "match_score": match.get("match_score", 0),
                "offer": offer_data["offer"],
                "explanation": offer_data["explanation"],
                "status": "Pending Approval"
            }
            
            # Store the offer in the database
            await self.store_offer(offer_record)
            
            return offer_record
        
        except Exception as e:
            logger.error(f"Error generating offer for candidate {candidate.get('name', 'Unknown')} and role {role.get('title', 'Unknown')}: {str(e)}")
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
    
    async def get_market_data(self, role_title: str, department: str, location: str, experience: str) -> str:
        """Get market data for a role using LLM."""
        try:
            response = await self.market_data_chain.arun(
                role_title=role_title,
                department=department,
                location=location,
                experience=experience
            )
            
            return response
        
        except Exception as e:
            logger.error(f"Error getting market data: {str(e)}")
            return "Market data not available."
    
    async def store_offer(self, offer_record: Dict[str, Any]):
        """Store the offer in the database."""
        try:
            offer_collection = get_offer_collection()
            
            # Check if offer already exists
            existing_offer = await offer_collection.find_one({
                "candidate_id": offer_record["candidate_id"],
                "role_id": offer_record["role_id"]
            })
            
            if existing_offer:
                # Update existing offer
                await offer_collection.update_one(
                    {"_id": existing_offer["_id"]},
                    {"$set": {
                        "match_score": offer_record["match_score"],
                        "offer": offer_record["offer"],
                        "explanation": offer_record["explanation"],
                        "status": offer_record["status"],
                        "updated_at": datetime.utcnow()
                    }}
                )
                logger.info(f"Updated existing offer: {existing_offer['_id']}")
            else:
                # Insert new offer
                offer_record["created_at"] = datetime.utcnow()
                offer_record["updated_at"] = datetime.utcnow()
                
                # Calculate start date if not provided
                if not offer_record["offer"].get("start_date"):
                    start_date = datetime.utcnow() + timedelta(days=30)  # Default to 30 days from now
                    offer_record["offer"]["start_date"] = start_date.strftime("%Y-%m-%d")
                
                result = await offer_collection.insert_one(offer_record)
                logger.info(f"Inserted new offer with ID: {result.inserted_id}")
        
        except Exception as e:
            logger.error(f"Error storing offer record: {str(e)}")