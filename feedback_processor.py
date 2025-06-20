# app/agents/feedback_processor.py
import logging
import json
from typing import Dict, Any, List
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import ChatPromptTemplate
from langchain.chains import LLMChain
from bson import ObjectId
from datetime import datetime

from app.core.config import settings
from app.db.mongodb import get_candidate_collection, get_role_collection, get_match_collection, get_offer_collection, get_feedback_collection

logger = logging.getLogger(__name__)

class FeedbackProcessorAgent:
    """Agent to collect and process HR feedback to fine-tune the system."""
    
    def __init__(self):
        # Initialize Gemini model
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-pro",
            temperature=0.2,
            google_api_key=settings.GOOGLE_API_KEY
        )
        
        # Set up feedback analysis prompt
        self.feedback_analysis_prompt = ChatPromptTemplate.from_template(
            """You are an AI learning system analyzing HR feedback to improve recommendations.
            Your goal is to extract actionable insights from HR feedback to fine-tune future matches and offers.
            
            # Feedback Information:
            Entity Type: {entity_type} (match or offer)
            Feedback Type: {feedback_type} (approval, rejection, modification)
            Comments: {comments}
            Modifications: {modifications}
            
            # Entity Details:
            {entity_details}
            
            Task: Analyze this feedback and provide:
            1. Key learnings from this feedback
            2. Specific patterns to reinforce or avoid in future recommendations
            3. Parameter adjustments that should be made to the system
            
            Format your response as a valid JSON object with fields:
            - learnings (array of string insights)
            - patterns (object with "reinforce" and "avoid" arrays)
            - parameters (object with parameter name keys and adjustment values)
            """
        )
        
        self.feedback_analysis_chain = LLMChain(
            llm=self.llm,
            prompt=self.feedback_analysis_prompt
        )
    
    async def process_feedback(self, feedback_id: str):
        """Process a specific feedback submission."""
        try:
            # Get feedback details
            feedback_collection = get_feedback_collection()
            feedback = await feedback_collection.find_one({"_id": ObjectId(feedback_id)})
            
            if not feedback:
                logger.error(f"Feedback not found: {feedback_id}")
                return None
            
            # Get entity details (match or offer)
            entity_details = await self.get_entity_details(
                feedback["entity_type"],
                feedback["entity_id"]
            )
            
            if not entity_details:
                logger.error(f"Entity not found for feedback: {feedback_id}")
                return None
            
            # Analyze the feedback
            analysis = await self.analyze_feedback(feedback, entity_details)
            
            # Store analysis with feedback
            await feedback_collection.update_one(
                {"_id": ObjectId(feedback_id)},
                {"$set": {"analysis": analysis}}
            )
            
            # Apply feedback to improve the system
            await self.apply_feedback(feedback, analysis)
            
            return analysis
        
        except Exception as e:
            logger.error(f"Error processing feedback: {str(e)}")
            return None
    
    async def get_entity_details(self, entity_type: str, entity_id: ObjectId) -> Dict[str, Any]:
        """Get details about the entity (match or offer) that received feedback."""
        try:
            if entity_type == "match":
                match_collection = get_match_collection()
                candidate_collection = get_candidate_collection()
                role_collection = get_role_collection()
                
                match = await match_collection.find_one({"_id": entity_id})
                if not match:
                    return None
                
                candidate = await candidate_collection.find_one({"_id": match["candidate_id"]})
                role = await role_collection.find_one({"_id": match["role_id"]})
                
                return {
                    "type": "match",
                    "match": match,
                    "candidate": candidate,
                    "role": role
                }
            
            elif entity_type == "offer":
                offer_collection = get_offer_collection()
                candidate_collection = get_candidate_collection()
                role_collection = get_role_collection()
                
                offer = await offer_collection.find_one({"_id": entity_id})
                if not offer:
                    return None
                
                candidate = await candidate_collection.find_one({"_id": offer["candidate_id"]})
                role = await role_collection.find_one({"_id": offer["role_id"]})
                
                return {
                    "type": "offer",
                    "offer": offer,
                    "candidate": candidate,
                    "role": role
                }
            
            else:
                logger.error(f"Unknown entity type: {entity_type}")
                return None
        
        except Exception as e:
            logger.error(f"Error getting entity details: {str(e)}")
            return None
    
    async def analyze_feedback(self, feedback: Dict[str, Any], entity_details: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze feedback using LLM."""
        try:
            # Format entity details for LLM
            entity_details_str = self.format_entity_details(entity_details)
            
            # Format modifications for LLM
            modifications_str = json.dumps(feedback.get("modifications", {}))
            
            # Run the analysis chain
            response = await self.feedback_analysis_chain.arun(
                entity_type=feedback["entity_type"],
                feedback_type=feedback["feedback_type"],
                comments=feedback.get("comments", ""),
                modifications=modifications_str,
                entity_details=entity_details_str
            )
            
            # Parse the response
            analysis = json.loads(response)
            
            return analysis
        
        except Exception as e:
            logger.error(f"Error analyzing feedback: {str(e)}")
            return {
                "learnings": [f"Error analyzing feedback: {str(e)}"],
                "patterns": {"reinforce": [], "avoid": []},
                "parameters": {}
            }
    
    async def apply_feedback(self, feedback: Dict[str, Any], analysis: Dict[str, Any]):
        """Apply feedback to improve the system."""
        try:
            # Update entity status based on feedback type
            if feedback["feedback_type"] == "approval":
                await self.update_entity_status(
                    feedback["entity_type"],
                    feedback["entity_id"],
                    "Approved"
                )
            
            elif feedback["feedback_type"] == "rejection":
                await self.update_entity_status(
                    feedback["entity_type"],
                    feedback["entity_id"],
                    "Rejected"
                )
            
            elif feedback["feedback_type"] == "modification":
                # Apply modifications
                await self.apply_modifications(
                    feedback["entity_type"],
                    feedback["entity_id"],
                    feedback.get("modifications", {})
                )
            
            # Store learnings in a knowledge base for future improvements
            await self.store_learnings(analysis)
            
            logger.info(f"Applied feedback {feedback['_id']} successfully")
        
        except Exception as e:
            logger.error(f"Error applying feedback: {str(e)}")
    
    def format_entity_details(self, entity_details: Dict[str, Any]) -> str:
        """Format entity details as text for the LLM."""
        if entity_details["type"] == "match":
            match = entity_details["match"]
            candidate = entity_details["candidate"]
            role = entity_details["role"]
            
            return f"""
            Entity Type: Match
            
            Match Details:
            Match Score: {match.get("match_score", 0)}
            Status: {match.get("status", "Unknown")}
            Matched Skills: {', '.join(match.get("skill_match", {}).get("matched", []))}
            Missing Skills: {', '.join(match.get("skill_match", {}).get("missing", []))}
            
            Candidate:
            Name: {candidate.get("name", "Unknown")}
            Experience: {candidate.get("experience", "Not specified")}
            Skills: {', '.join(candidate.get("skills", []))}
            
            Role:
            Title: {role.get("title", "Unknown")}
            Department: {role.get("department", "Unknown")}
            Required Skills: {', '.join(role.get("required_skills", []))}
            """
        
        elif entity_details["type"] == "offer":
            offer = entity_details["offer"]
            candidate = entity_details["candidate"]
            role = entity_details["role"]
            
            return f"""
            Entity Type: Offer
            
            Offer Details:
            Base Salary: {offer.get("offer", {}).get("base_salary", "Not specified")}
            Bonus: {offer.get("offer", {}).get("bonus", "Not specified")}
            Equity: {offer.get("offer", {}).get("equity", "Not specified")}
            Total CTC: {offer.get("offer", {}).get("total_ctc", "Not specified")}
            Work Arrangement: {offer.get("offer", {}).get("remote", "Not specified")}
            Status: {offer.get("status", "Unknown")}
            
            Candidate:
            Name: {candidate.get("name", "Unknown")}
            Experience: {candidate.get("experience", "Not specified")}
            Current CTC: {candidate.get("current_ctc", "Not specified")}
            Expected CTC: {candidate.get("expected_ctc", "Not specified")}
            
            Role:
            Title: {role.get("title", "Unknown")}
            Department: {role.get("department", "Unknown")}
            Location: {role.get("location", "Not specified")}
            """
        
        else:
            return "Unknown entity type"
    
    async def update_entity_status(self, entity_type: str, entity_id: ObjectId, status: str):
        """Update the status of an entity (match or offer)."""
        try:
            if entity_type == "match":
                match_collection = get_match_collection()
                await match_collection.update_one(
                    {"_id": entity_id},
                    {"$set": {"status": status, "updated_at": datetime.utcnow()}}
                )
            
            elif entity_type == "offer":
                offer_collection = get_offer_collection()
                await offer_collection.update_one(
                    {"_id": entity_id},
                    {"$set": {"status": status, "updated_at": datetime.utcnow()}}
                )
            
            logger.info(f"Updated {entity_type} {entity_id} status to {status}")
        
        except Exception as e:
            logger.error(f"Error updating entity status: {str(e)}")
    
    async def apply_modifications(self, entity_type: str, entity_id: ObjectId, modifications: Dict[str, Any]):
        """Apply modifications to an entity (match or offer)."""
        try:
            if entity_type == "match":
                match_collection = get_match_collection()
                
                update_data = {}
                for key, value in modifications.items():
                    update_data[key] = value
                
                update_data["status"] = "Modified"
                update_data["updated_at"] = datetime.utcnow()
                
                await match_collection.update_one(
                    {"_id": entity_id},
                    {"$set": update_data}
                )
            
            elif entity_type == "offer":
                offer_collection = get_offer_collection()
                
                # For offers, modifications might be nested in the offer field
                update_data = {}
                for key, value in modifications.items():
                    if key.startswith("offer."):
                        # Handle nested updates (e.g., offer.base_salary)
                        nested_key = key.split(".", 1)[1]
                        update_data[f"offer.{nested_key}"] = value
                    else:
                        update_data[key] = value
                
                update_data["status"] = "Modified"
                update_data["updated_at"] = datetime.utcnow()
                
                await offer_collection.update_one(
                    {"_id": entity_id},
                    {"$set": update_data}
                )
            
            logger.info(f"Applied modifications to {entity_type} {entity_id}")
        
        except Exception as e:
            logger.error(f"Error applying modifications: {str(e)}")
    
    async def store_learnings(self, analysis: Dict[str, Any]):
        """Store learnings in a knowledge base for future improvements."""
        try:
            # In a real implementation, you might want to:
            # 1. Store learnings in a vector database for semantic retrieval
            # 2. Update a model fine-tuning dataset
            # 3. Create a knowledge base collection in MongoDB
            
            # For this implementation, we'll just log the learnings
            logger.info(f"Learnings from feedback: {analysis.get('learnings', [])}")
            logger.info(f"Patterns to reinforce: {analysis.get('patterns', {}).get('reinforce', [])}")
            logger.info(f"Patterns to avoid: {analysis.get('patterns', {}).get('avoid', [])}")
            logger.info(f"Parameter adjustments: {analysis.get('parameters', {})}")
            
            # TODO: In a full implementation, store these in MongoDB or Pinecone
            # Example:
            # learnings_collection = mongodb.db.learnings
            # await learnings_collection.insert_one({
            #     "timestamp": datetime.utcnow(),
            #     "learnings": analysis.get("learnings", []),
            #     "patterns": analysis.get("patterns", {}),
            #     "parameters": analysis.get("parameters", {})
            # })
        
        except Exception as e:
            logger.error(f"Error storing learnings: {str(e)}")
    
    async def process_pending_feedback(self):
        """Process all pending feedback."""
        try:
            feedback_collection = get_feedback_collection()
            
            # Find feedback without analysis
            pending_feedback = await feedback_collection.find(
                {"analysis": {"$exists": False}}
            ).to_list(100)
            
            logger.info(f"Processing {len(pending_feedback)} pending feedback items")
            
            for feedback in pending_feedback:
                await self.process_feedback(str(feedback["_id"]))
            
            return len(pending_feedback)
        
        except Exception as e:
            logger.error(f"Error processing pending feedback: {str(e)}")
            return 0