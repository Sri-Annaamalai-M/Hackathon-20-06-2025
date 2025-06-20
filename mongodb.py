# app/db/mongodb.py
import logging
from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings

logger = logging.getLogger(__name__)

class MongoDB:
    client: AsyncIOMotorClient = None
    db = None

mongodb = MongoDB()

async def connect_to_mongo():
    """Create database connection."""
    logger.info("Connecting to MongoDB...")
    mongodb.client = AsyncIOMotorClient(settings.MONGODB_URL)
    mongodb.db = mongodb.client[settings.MONGODB_DB_NAME]
    logger.info("Connected to MongoDB!")

    # Set up collections
    await setup_collections()

async def close_mongo_connection():
    """Close database connection."""
    logger.info("Closing MongoDB connection...")
    if mongodb.client:
        mongodb.client.close()
    logger.info("MongoDB connection closed!")

async def setup_collections():
    """Set up collections and indexes."""
    # Create collections if they don't exist
    collections = [
        "candidates", 
        "roles", 
        "matches", 
        "offers", 
        "feedback", 
        "vectors"  # Added vectors collection
    ]
    
    for collection_name in collections:
        # Check if collection exists, if not create it
        if collection_name not in await mongodb.db.list_collection_names():
            await mongodb.db.create_collection(collection_name)
            logger.info(f"Created collection: {collection_name}")
    
    # Create indexes
    # Candidates collection
    await mongodb.db.candidates.create_index("email", unique=True)
    
    # Roles collection
    await mongodb.db.roles.create_index("title")
    
    # Matches collection
    await mongodb.db.matches.create_index([("candidate_id", 1), ("role_id", 1)], unique=True)
    
    # Offers collection
    await mongodb.db.offers.create_index([("candidate_id", 1), ("role_id", 1)], unique=True)
    
    # Vectors collection
    await mongodb.db.vectors.create_index("vector_id", unique=True)
    await mongodb.db.vectors.create_index("type")
    
    logger.info("Database collections and indexes set up successfully")

# Helper functions to get collection references
def get_candidate_collection():
    return mongodb.db.candidates

def get_role_collection():
    return mongodb.db.roles

def get_match_collection():
    return mongodb.db.matches

def get_offer_collection():
    return mongodb.db.offers

def get_feedback_collection():
    return mongodb.db.feedback

def get_vector_collection():
    return mongodb.db.vectors