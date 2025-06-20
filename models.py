# app/schemas/models.py
from typing import List, Optional, Dict, Any, Annotated
from datetime import datetime
from pydantic import BaseModel, Field, EmailStr, model_validator, field_serializer
from bson import ObjectId

# Custom ObjectId field for MongoDB compatibility
class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        # For backwards compatibility with Pydantic v1
        yield cls.validate
    
    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)
    
    @classmethod
    def __get_pydantic_json_schema__(cls, _schema_generator):
        # This replaces __modify_schema__ in Pydantic v2
        return {"type": "string"}

# Base model with ID field
class MongoBaseModel(BaseModel):
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")

    # Define serializer for ObjectId
    @field_serializer('id')
    def serialize_id(self, id: PyObjectId, _info):
        return str(id)
    
    class Config:
        # For Pydantic v2, validate_by_name replaces allow_population_by_field_name
        validate_by_name = True
        # For Pydantic v2, json_schema_extra replaces schema_extra
        json_schema_extra = {"populate_by_name": True}

# Candidate models
class CandidateBase(BaseModel):
    name: str
    email: EmailStr
    phone: Optional[str] = None
    skills: List[str] = []
    experience: Optional[str] = None
    education: Optional[str] = None
    certifications: Optional[List[str]] = None
    current_ctc: Optional[float] = None
    expected_ctc: Optional[float] = None
    notice_period: Optional[int] = None
    location: Optional[str] = None
    remote_preference: Optional[str] = None
    interview_scores: Optional[Dict[str, float]] = None
    interview_feedback: Optional[str] = None
    preferences: Optional[Dict[str, Any]] = None

class CandidateCreate(CandidateBase):
    pass

class CandidateInDB(MongoBaseModel, CandidateBase):
    resume_path: Optional[str] = None
    interview_notes_path: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class CandidateUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    skills: Optional[List[str]] = None
    experience: Optional[str] = None
    education: Optional[str] = None
    certifications: Optional[List[str]] = None
    current_ctc: Optional[float] = None
    expected_ctc: Optional[float] = None
    notice_period: Optional[int] = None
    location: Optional[str] = None
    remote_preference: Optional[str] = None
    interview_scores: Optional[Dict[str, float]] = None
    interview_feedback: Optional[str] = None
    preferences: Optional[Dict[str, Any]] = None
    resume_path: Optional[str] = None
    interview_notes_path: Optional[str] = None

class CandidateResponse(CandidateInDB):
    pass

# Role models
class RoleBase(BaseModel):
    title: str
    department: str
    description: Optional[str] = None
    required_skills: List[str] = []
    preferred_skills: Optional[List[str]] = None
    experience_required: Optional[str] = None
    education_required: Optional[str] = None
    certifications_required: Optional[List[str]] = None
    salary_range: Optional[Dict[str, float]] = None
    location: Optional[str] = None
    remote_option: Optional[str] = None
    team_size: Optional[int] = None
    hiring_manager: Optional[str] = None

class RoleCreate(RoleBase):
    pass

class RoleInDB(MongoBaseModel, RoleBase):
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class RoleUpdate(BaseModel):
    title: Optional[str] = None
    department: Optional[str] = None
    description: Optional[str] = None
    required_skills: Optional[List[str]] = None
    preferred_skills: Optional[List[str]] = None
    experience_required: Optional[str] = None
    education_required: Optional[str] = None
    certifications_required: Optional[List[str]] = None
    salary_range: Optional[Dict[str, float]] = None
    location: Optional[str] = None
    remote_option: Optional[str] = None
    team_size: Optional[int] = None
    hiring_manager: Optional[str] = None
    is_active: Optional[bool] = None

class RoleResponse(RoleInDB):
    pass

# Match models
class SkillMatch(BaseModel):
    matched: List[str] = []
    missing: List[str] = []

class MatchBase(BaseModel):
    candidate_id: PyObjectId
    role_id: PyObjectId
    match_score: float
    skill_match: SkillMatch
    explanation: str
    status: str = "Pending"

    # Define serializer for ObjectId fields
    @field_serializer('candidate_id', 'role_id')
    def serialize_objectid(self, id: PyObjectId, _info):
        return str(id)

class MatchCreate(MatchBase):
    pass

class MatchInDB(MongoBaseModel, MatchBase):
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class MatchUpdate(BaseModel):
    match_score: Optional[float] = None
    skill_match: Optional[SkillMatch] = None
    explanation: Optional[str] = None
    status: Optional[str] = None

class MatchWithDetails(MatchInDB):
    candidate: CandidateResponse
    role: RoleResponse

class MatchResponse(MatchInDB):
    pass

# Offer models
class OfferDetails(BaseModel):
    base_salary: float
    bonus: Optional[float] = 0
    equity: Optional[str] = None
    benefits: List[str] = []
    total_ctc: float
    start_date: Optional[str] = None
    remote: Optional[str] = None

class OfferBase(BaseModel):
    candidate_id: PyObjectId
    role_id: PyObjectId
    match_id: PyObjectId
    match_score: float
    offer: OfferDetails
    explanation: str
    status: str = "Pending Approval"

    # Define serializer for ObjectId fields
    @field_serializer('candidate_id', 'role_id', 'match_id')
    def serialize_objectid(self, id: PyObjectId, _info):
        return str(id)

class OfferCreate(OfferBase):
    pass

class OfferInDB(MongoBaseModel, OfferBase):
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class OfferUpdate(BaseModel):
    offer: Optional[OfferDetails] = None
    explanation: Optional[str] = None
    status: Optional[str] = None

class OfferWithDetails(OfferInDB):
    candidate: CandidateResponse
    role: RoleResponse

class OfferResponse(OfferInDB):
    pass

# Feedback models
class FeedbackBase(BaseModel):
    entity_type: str  # 'match' or 'offer'
    entity_id: PyObjectId
    feedback_type: str  # 'approval', 'rejection', 'modification'
    comments: Optional[str] = None
    modifications: Optional[Dict[str, Any]] = None

    # Define serializer for ObjectId fields
    @field_serializer('entity_id')
    def serialize_objectid(self, id: PyObjectId, _info):
        return str(id)

class FeedbackCreate(FeedbackBase):
    pass

class FeedbackInDB(MongoBaseModel, FeedbackBase):
    created_at: datetime = Field(default_factory=datetime.utcnow)

class FeedbackResponse(FeedbackInDB):
    pass