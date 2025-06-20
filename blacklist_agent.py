# app/agents/blacklist_agent.py
import logging
from typing import Dict, Any, List
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import ChatPromptTemplate
from langchain.chains import LLMChain
from bson import ObjectId

from app.core.config import settings
from app.db.mongodb import get_candidate_collection, get_role_collection

logger = logging.getLogger(__name__)

class BlacklistAgent:
    """Agent to filter out candidates who do not meet minimum role criteria."""
    
    def __init__(self):
        # Initialize Gemini model
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-pro",
            temperature=0.1,  # Low temperature for consistent filtering decisions
            google_api_key=settings.GOOGLE_API_KEY
        )
        
        # Set up blacklist evaluation prompt
        self.blacklist_prompt = ChatPromptTemplate.from_template(
            """You are an AI system responsible for filtering out candidates who do not meet minimum role requirements.
            
            # Candidate Profile:
            {candidate_profile}
            
            # Job Role:
            {role_profile}
            
            # Blacklist Criteria:
            1. Missing critical required experience (e.g., years of experience below minimum)
            2. Location conflict (e.g., remote-only candidate for on-site role)
            3. Missing mandatory skills (e.g., lacking core technical skills)
            4. Education mismatch (e.g., missing required degree)
            5. Certification mismatch (e.g., missing required certifications)
            
            Task: Evaluate if this candidate should be blacklisted for this role.
            
            Format your response as a valid JSON object with fields:
            - blacklist (boolean): true if candidate should be blacklisted, false otherwise
            - reason (string): clear explanation of blacklist decision (only if blacklist is true)
            - severity (string): "hard" for definite rejections, "soft" for borderline cases (only if blacklist is true)
            """
        )
        
        self.blacklist_chain = LLMChain(
            llm=self.llm,
            prompt=self.blacklist_prompt
        )
    
    async def evaluate_candidate(self, candidate: Dict[str, Any], role: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate if a candidate should be blacklisted for a specific role."""
        try:
            # Format candidate profile as text
            candidate_profile = self.format_candidate_profile(candidate)
            
            # Format role profile as text
            role_profile = self.format_role_profile(role)
            
            # Run the blacklist chain
            response = await self.blacklist_chain.arun(
                candidate_profile=candidate_profile,
                role_profile=role_profile
            )
            
            # Parse the response
            import json
            blacklist_data = json.loads(response)
            
            # Add candidate and role info
            blacklist_data["candidate_id"] = candidate["_id"]
            blacklist_data["candidate_name"] = candidate.get("name", "Unknown")
            blacklist_data["role_id"] = role["_id"]
            blacklist_data["role_title"] = role.get("title", "Unknown")
            
            return blacklist_data
        
        except Exception as e:
            logger.error(f"Error evaluating blacklist for candidate {candidate.get('name', 'Unknown')} and role {role.get('title', 'Unknown')}: {str(e)}")
            # Default to not blacklisting if there's an error (fail open)
            return {
                "blacklist": False,
                "candidate_id": candidate["_id"],
                "candidate_name": candidate.get("name", "Unknown"),
                "role_id": role["_id"],
                "role_title": role.get("title", "Unknown")
            }
    
    async def batch_evaluate(self, candidate_ids=None, role_ids=None) -> List[Dict[str, Any]]:
        """Batch evaluate multiple candidates against multiple roles."""
        try:
            # Get collections
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
            
            logger.info(f"Evaluating {len(candidates)} candidates against {len(roles)} roles for blacklisting")
            
            results = []
            
            # Process each candidate against each role
            for candidate in candidates:
                for role in roles:
                    result = await self.evaluate_candidate(candidate, role)
                    results.append(result)
            
            return results
        
        except Exception as e:
            logger.error(f"Error in batch blacklist evaluation: {str(e)}")
            return []
    
    def format_candidate_profile(self, candidate: Dict[str, Any]) -> str:
        """Format candidate profile as text for the LLM."""
        return f"""
        Name: {candidate.get('name', 'Unknown')}
        Email: {candidate.get('email', 'Unknown')}
        Skills: {', '.join(candidate.get('skills', []))}
        Experience: {candidate.get('experience', 'Not specified')}
        Education: {candidate.get('education', 'Not specified')}
        Certifications: {', '.join(candidate.get('certifications', []) or [])}
        Location: {candidate.get('location', 'Not specified')}
        Remote Preference: {candidate.get('remote_preference', 'Not specified')}
        """
    
    def format_role_profile(self, role: Dict[str, Any]) -> str:
        """Format role profile as text for the LLM."""
        return f"""
        Title: {role.get('title', 'Unknown')}
        Department: {role.get('department', 'Unknown')}
        Required Skills: {', '.join(role.get('required_skills', []))}
        Preferred Skills: {', '.join(role.get('preferred_skills', []) or [])}
        Experience Required: {role.get('experience_required', 'Not specified')}
        Education Required: {role.get('education_required', 'Not specified')}
        Certifications Required: {', '.join(role.get('certifications_required', []) or [])}
        Location: {role.get('location', 'Not specified')}
        Remote Option: {role.get('remote_option', 'Not specified')}
        """
    
    def should_blacklist(self, candidate: Dict[str, Any], role: Dict[str, Any]) -> bool:
        """Rule-based quick check if a candidate should be blacklisted.
        
        This is a simpler, rule-based version that can be used for quick filtering
        without calling the LLM for every candidate-role pair.
        """
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
        
        # 3. Missing mandatory education
        if (role.get("education_required") and 
            role.get("education_required").lower() not in (candidate.get("education") or "").lower()):
            # Only if it's a strict requirement (indicated by "required" in the field)
            if "required" in role.get("education_required", "").lower():
                return True
        
        # 4. Missing mandatory certifications
        required_certs = role.get("certifications_required", [])
        candidate_certs = candidate.get("certifications", []) or []
        
        if required_certs:
            # Check if all required certifications are present
            if not all(cert.lower() in [c.lower() for c in candidate_certs] for cert in required_certs):
                # Only if they're explicitly marked as mandatory
                if role.get("certifications_mandatory", False):
                    return True
        
        return False