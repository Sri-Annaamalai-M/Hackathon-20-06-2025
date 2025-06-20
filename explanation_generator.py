# app/agents/explanation_generator.py
import logging
from typing import Dict, Any, List
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import ChatPromptTemplate
from langchain.chains import LLMChain
from bson import ObjectId

from app.core.config import settings
from app.db.mongodb import get_candidate_collection, get_role_collection, get_match_collection, get_offer_collection

logger = logging.getLogger(__name__)

class ExplanationGeneratorAgent:
    """Agent to produce human-readable justifications for role matches and offer recommendations."""
    
    def __init__(self):
        # Initialize Gemini model
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-pro",
            temperature=0.3,
            google_api_key=settings.GOOGLE_API_KEY
        )
        
        # Set up match explanation prompt
        self.match_explanation_prompt = ChatPromptTemplate.from_template(
            """You are an expert HR professional explaining role match decisions to a hiring manager.
            Your goal is to provide clear, concise, and insightful explanations that highlight key factors.
            
            # Candidate Profile:
            {candidate_profile}
            
            # Job Role:
            {role_profile}
            
            # Match Information:
            Match Score: {match_score}
            Matched Skills: {matched_skills}
            Missing Skills: {missing_skills}
            
            Task: Generate a comprehensive explanation that covers:
            1. Why this candidate is a good fit for the role (skills, experience, education)
            2. Specific strengths that make them stand out
            3. Any potential concerns or skill gaps
            4. How their preferences align with the role requirements
            
            Make your explanation HR-friendly, factual, and balanced. Aim for 2-3 paragraphs.
            """
        )
        
        self.match_explanation_chain = LLMChain(
            llm=self.llm,
            prompt=self.match_explanation_prompt
        )
        
        # Set up offer explanation prompt
        self.offer_explanation_prompt = ChatPromptTemplate.from_template(
            """You are an expert HR compensation analyst explaining an offer package to a hiring manager.
            Your goal is to provide clear, concise, and insightful explanations that justify the offer components.
            
            # Candidate Profile:
            {candidate_profile}
            
            # Job Role:
            {role_profile}
            
            # Match Information:
            Match Score: {match_score}
            
            # Offer Package:
            {offer_package}
            
            Task: Generate a comprehensive explanation that covers:
            1. Why this offer package is appropriate for the candidate
            2. How it aligns with market standards for the role and location
            3. Justification for the salary, bonus, and equity components
            4. Reasoning behind benefits and work arrangement decisions
            5. How the offer accounts for candidate's current compensation and expectations
            
            Make your explanation HR-friendly, factual, and balanced. Aim for 2-3 paragraphs.
            """
        )
        
        self.offer_explanation_chain = LLMChain(
            llm=self.llm,
            prompt=self.offer_explanation_prompt
        )
    
    async def generate_match_explanation(self, match_id: str) -> str:
        """Generate an explanation for a specific match."""
        try:
            # Get collections
            match_collection = get_match_collection()
            candidate_collection = get_candidate_collection()
            role_collection = get_role_collection()
            
            # Get match details
            match = await match_collection.find_one({"_id": ObjectId(match_id)})
            if not match:
                logger.error(f"Match not found: {match_id}")
                return "Match not found."
            
            # Get candidate and role details
            candidate = await candidate_collection.find_one({"_id": match["candidate_id"]})
            role = await role_collection.find_one({"_id": match["role_id"]})
            
            if not candidate or not role:
                logger.error(f"Candidate or role not found for match {match_id}")
                return "Candidate or role not found."
            
            # Format candidate profile as text
            candidate_profile = self.format_candidate_profile(candidate)
            
            # Format role profile as text
            role_profile = self.format_role_profile(role)
            
            # Get matched and missing skills
            matched_skills = ", ".join(match.get("skill_match", {}).get("matched", []))
            missing_skills = ", ".join(match.get("skill_match", {}).get("missing", []))
            
            # Run the explanation chain
            explanation = await self.match_explanation_chain.arun(
                candidate_profile=candidate_profile,
                role_profile=role_profile,
                match_score=match.get("match_score", 0),
                matched_skills=matched_skills,
                missing_skills=missing_skills
            )
            
            # Update the match with the explanation
            await match_collection.update_one(
                {"_id": ObjectId(match_id)},
                {"$set": {"explanation": explanation}}
            )
            
            return explanation
        
        except Exception as e:
            logger.error(f"Error generating match explanation: {str(e)}")
            return f"Error generating explanation: {str(e)}"
    
    async def generate_offer_explanation(self, offer_id: str) -> str:
        """Generate an explanation for a specific offer."""
        try:
            # Get collections
            offer_collection = get_offer_collection()
            candidate_collection = get_candidate_collection()
            role_collection = get_role_collection()
            
            # Get offer details
            offer = await offer_collection.find_one({"_id": ObjectId(offer_id)})
            if not offer:
                logger.error(f"Offer not found: {offer_id}")
                return "Offer not found."
            
            # Get candidate and role details
            candidate = await candidate_collection.find_one({"_id": offer["candidate_id"]})
            role = await role_collection.find_one({"_id": offer["role_id"]})
            
            if not candidate or not role:
                logger.error(f"Candidate or role not found for offer {offer_id}")
                return "Candidate or role not found."
            
            # Format candidate profile as text
            candidate_profile = self.format_candidate_profile(candidate)
            
            # Format role profile as text
            role_profile = self.format_role_profile(role)
            
            # Format offer package
            offer_package = self.format_offer_package(offer.get("offer", {}))
            
            # Run the explanation chain
            explanation = await self.offer_explanation_chain.arun(
                candidate_profile=candidate_profile,
                role_profile=role_profile,
                match_score=offer.get("match_score", 0),
                offer_package=offer_package
            )
            
            # Update the offer with the explanation
            await offer_collection.update_one(
                {"_id": ObjectId(offer_id)},
                {"$set": {"explanation": explanation}}
            )
            
            return explanation
        
        except Exception as e:
            logger.error(f"Error generating offer explanation: {str(e)}")
            return f"Error generating explanation: {str(e)}"
    
    async def batch_generate_explanations(self, type_filter: str = "all"):
        """Generate explanations for all matches or offers that don't have them yet."""
        try:
            if type_filter in ["all", "match"]:
                # Process matches
                match_collection = get_match_collection()
                matches = await match_collection.find({"explanation": {"$exists": False}}).to_list(100)
                
                for match in matches:
                    await self.generate_match_explanation(str(match["_id"]))
                
                logger.info(f"Generated explanations for {len(matches)} matches")
            
            if type_filter in ["all", "offer"]:
                # Process offers
                offer_collection = get_offer_collection()
                offers = await offer_collection.find({"explanation": {"$exists": False}}).to_list(100)
                
                for offer in offers:
                    await self.generate_offer_explanation(str(offer["_id"]))
                
                logger.info(f"Generated explanations for {len(offers)} offers")
        
        except Exception as e:
            logger.error(f"Error in batch explanation generation: {str(e)}")
    
    def format_candidate_profile(self, candidate: Dict[str, Any]) -> str:
        """Format candidate profile as text for the LLM."""
        import json
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
        import json
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
        """
    
    def format_offer_package(self, offer: Dict[str, Any]) -> str:
        """Format offer package as text for the LLM."""
        return f"""
        Base Salary: {offer.get('base_salary', 'Not specified')}
        Bonus: {offer.get('bonus', 'Not specified')}
        Equity: {offer.get('equity', 'Not specified')}
        Benefits: {', '.join(offer.get('benefits', []))}
        Total CTC: {offer.get('total_ctc', 'Not specified')}
        Start Date: {offer.get('start_date', 'Not specified')}
        Work Arrangement: {offer.get('remote', 'Not specified')}
        """