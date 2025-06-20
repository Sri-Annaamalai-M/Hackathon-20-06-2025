# app/agents/profile_parser.py
import os
import logging
import json
import asyncio
import uuid
from typing import List, Dict, Any
from datetime import datetime
import docx2txt
import PyPDF2
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import ChatPromptTemplate
from langchain.chains import LLMChain
from langchain.schema import Document
from sentence_transformers import SentenceTransformer

from app.core.config import settings
from app.db.mongodb import get_candidate_collection
from app.db.vector_store import MongoDBVectorStore  # Use MongoDB instead of Pinecone

logger = logging.getLogger(__name__)

class ProfileParserAgent:
    """Agent to parse candidate profiles from resumes and interview notes."""
    
    def __init__(self):
        # Initialize Gemini model
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-pro",
            temperature=0,
            google_api_key=settings.GOOGLE_API_KEY
        )
        
        # Use SentenceTransformer for embeddings
        self.sentence_model = SentenceTransformer('all-MiniLM-L6-v2')
            
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=100
        )
        
        # Set up parsing prompt
        self.parse_prompt = ChatPromptTemplate.from_template(
            """You are an expert in parsing resumes and extracting structured information.
            Extract the following information from the provided resume or interview notes:
            
            1. Name
            2. Email
            3. Phone
            4. Skills (technical, soft, domain-specific)
            5. Work Experience (roles, companies, duration)
            6. Education (degrees, institutions, years)
            7. Certifications
            8. Current CTC (if mentioned)
            9. Expected CTC (if mentioned)
            10. Notice Period (if mentioned)
            11. Location
            12. Remote Work Preference (if mentioned)
            
            If the information is from interview notes, also extract:
            13. Interview Scores
            14. Interview Feedback
            15. Project Interests/Preferences
            
            Format your response as a valid JSON object with these fields. If a field is not found, use null.
            
            Resume/Interview Notes:
            {text}
            """
        )
        
        self.parser_chain = LLMChain(
            llm=self.llm,
            prompt=self.parse_prompt
        )
    
    async def process_files(self, files: List[Dict[str, str]]):
        """Process uploaded candidate files in the background."""
        logger.info(f"Starting to process {len(files)} files")
        
        try:
            # Group files by assumed candidate (based on filename patterns)
            # This is a simple approach - in production, you'd want more robust grouping
            candidate_files = {}
            
            for file in files:
                # Extract a candidate identifier (e.g., from filename)
                # Here we just use the first part of the filename before underscore
                filename = os.path.basename(file["path"])
                candidate_id = filename.split("_")[1] if "_" in filename else filename
                
                if candidate_id not in candidate_files:
                    candidate_files[candidate_id] = []
                
                candidate_files[candidate_id].append(file)
            
            # Process each candidate's files
            for candidate_id, files_list in candidate_files.items():
                await self.process_candidate_files(files_list)
        
        except Exception as e:
            logger.error(f"Error in profile parser background task: {str(e)}")
    
    async def process_candidate_files(self, files: List[Dict[str, str]]):
        """Process all files for a single candidate."""
        logger.info(f"Processing files for candidate: {files}")
        
        try:
            # Extract text from all files
            all_text = ""
            resume_path = None
            notes_path = None
            
            for file in files:
                file_path = file["path"]
                file_text = self.extract_text_from_file(file_path)
                all_text += file_text + "\n\n"
                
                # Keep track of file paths
                if "resumes" in file_path:
                    resume_path = file_path
                elif "notes" in file_path:
                    notes_path = file_path
            
            # Parse the combined text
            structured_profile = await self.parse_profile(all_text)
            
            if not structured_profile:
                logger.error("Failed to parse profile from files")
                return
            
            # Add file paths
            structured_profile["resume_path"] = resume_path
            structured_profile["interview_notes_path"] = notes_path
            
            # Store the candidate profile in MongoDB
            await self.store_candidate_profile(structured_profile)
            
            # Create embeddings for vector search
            await self.create_profile_embeddings(structured_profile)
            
            logger.info(f"Successfully processed candidate profile: {structured_profile.get('name', 'Unknown')}")
        
        except Exception as e:
            logger.error(f"Error processing candidate files: {str(e)}")
    
    def extract_text_from_file(self, file_path: str) -> str:
        """Extract text content from different file types."""
        try:
            file_extension = os.path.splitext(file_path)[1].lower()
            
            if file_extension == ".pdf":
                return self.extract_text_from_pdf(file_path)
            elif file_extension == ".docx":
                return self.extract_text_from_docx(file_path)
            else:
                # Assume it's a plain text file
                with open(file_path, "r", encoding="utf-8") as f:
                    return f.read()
        
        except Exception as e:
            logger.error(f"Error extracting text from file {file_path}: {str(e)}")
            return ""
    
    def extract_text_from_pdf(self, file_path: str) -> str:
        """Extract text from PDF file."""
        text = ""
        try:
            with open(file_path, "rb") as f:
                pdf_reader = PyPDF2.PdfReader(f)
                for page_num in range(len(pdf_reader.pages)):
                    text += pdf_reader.pages[page_num].extract_text() + "\n"
        except Exception as e:
            logger.error(f"Error extracting text from PDF {file_path}: {str(e)}")
        
        return text
    
    def extract_text_from_docx(self, file_path: str) -> str:
        """Extract text from DOCX file."""
        try:
            return docx2txt.process(file_path)
        except Exception as e:
            logger.error(f"Error extracting text from DOCX {file_path}: {str(e)}")
            return ""
    
    async def parse_profile(self, text: str) -> Dict[str, Any]:
        """Parse profile information from text using LLM."""
        try:
            response = await self.parser_chain.arun(text=text)
            
            # Parse the JSON response
            parsed_json = json.loads(response)
            
            # Convert keys to snake_case
            profile = {}
            key_mapping = {
                "Name": "name",
                "Email": "email",
                "Phone": "phone",
                "Skills": "skills",
                "WorkExperience": "experience",
                "Education": "education",
                "Certifications": "certifications",
                "CurrentCTC": "current_ctc",
                "ExpectedCTC": "expected_ctc",
                "NoticePeriod": "notice_period",
                "Location": "location",
                "RemoteWorkPreference": "remote_preference",
                "InterviewScores": "interview_scores",
                "InterviewFeedback": "interview_feedback",
                "ProjectInterests": "preferences"
            }
            
            for key, value in parsed_json.items():
                snake_key = key_mapping.get(key.replace(" ", ""), key.lower())
                profile[snake_key] = value
            
            return profile
        
        except Exception as e:
            logger.error(f"Error parsing profile: {str(e)}")
            return {}
    
    async def store_candidate_profile(self, profile: Dict[str, Any]):
        """Store candidate profile in MongoDB."""
        try:
            candidate_collection = get_candidate_collection()
            
            # Check if candidate already exists (by email)
            if profile.get("email"):
                existing_candidate = await candidate_collection.find_one({"email": profile["email"]})
                
                if existing_candidate:
                    # Update existing candidate
                    await candidate_collection.update_one(
                        {"_id": existing_candidate["_id"]},
                        {"$set": {**profile, "updated_at": datetime.utcnow()}}
                    )
                    logger.info(f"Updated existing candidate profile: {profile.get('name', 'Unknown')}")
                    return
            
            # Insert new candidate
            profile["created_at"] = datetime.utcnow()
            profile["updated_at"] = datetime.utcnow()
            
            result = await candidate_collection.insert_one(profile)
            logger.info(f"Inserted new candidate profile with ID: {result.inserted_id}")
        
        except Exception as e:
            logger.error(f"Error storing candidate profile: {str(e)}")
    
    async def create_profile_embeddings(self, profile: Dict[str, Any]):
        """Create embeddings for vector search using MongoDB."""
        try:
            # Create a text representation of the profile for embedding
            profile_text = f"""
            Name: {profile.get('name', '')}
            Email: {profile.get('email', '')}
            Skills: {', '.join(profile.get('skills', []))}
            Experience: {profile.get('experience', '')}
            Education: {profile.get('education', '')}
            Certifications: {', '.join(profile.get('certifications', []) or [])}
            Location: {profile.get('location', '')}
            Remote Preference: {profile.get('remote_preference', '')}
            """
            
            # Create embedding using SentenceTransformer
            embedding = self.sentence_model.encode(profile_text).tolist()
            
            # Store in MongoDB vector collection
            metadata = {
                "name": profile.get('name', ''),
                "email": profile.get('email', ''),
                "skills": profile.get('skills', []),
                "experience": profile.get('experience', ''),
                "education": profile.get('education', ''),
                "type": "candidate"
            }
            
            # Use email as ID for candidates
            vector_id = f"candidate_{profile.get('email', str(uuid.uuid4()))}"
            
            # Store the embedding in MongoDB
            await MongoDBVectorStore.store_embedding(vector_id, embedding, metadata)
            logger.info(f"Created embeddings for candidate: {profile.get('name', 'Unknown')}")
        
        except Exception as e:
            logger.error(f"Error creating profile embeddings: {str(e)}")