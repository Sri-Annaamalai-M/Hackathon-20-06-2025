# app/db/vector_store.py
import logging
import json
from typing import Dict, Any, List, Optional
from bson import ObjectId
import numpy as np
from app.core.config import settings
from app.db.mongodb import get_vector_collection

logger = logging.getLogger(__name__)

class MongoDBVectorStore:
    """MongoDB-based vector store for embeddings and semantic search."""
    
    @staticmethod
    async def init_vector_store():
        """Initialize the vector store (create indexes)."""
        try:
            vector_collection = get_vector_collection()
            
            # Create indexes for efficient lookups
            await vector_collection.create_index("vector_id", unique=True)
            await vector_collection.create_index("type")
            await vector_collection.create_index([("metadata.name", 1)])
            await vector_collection.create_index([("metadata.title", 1)])
            await vector_collection.create_index([("metadata.type", 1)])
            
            logger.info("MongoDB vector store initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Error initializing MongoDB vector store: {str(e)}")
            return False
    
    @staticmethod
    async def store_embedding(vector_id: str, vector: List[float], metadata: Optional[Dict] = None):
        """Store a vector embedding in MongoDB."""
        try:
            vector_collection = get_vector_collection()
            
            # Prepare the document
            document = {
                "vector_id": vector_id,
                "vector": vector,
                "metadata": metadata or {},
                "type": metadata.get("type") if metadata else "unknown"
            }
            
            # Check if vector already exists
            existing = await vector_collection.find_one({"vector_id": vector_id})
            
            if existing:
                # Update existing vector
                await vector_collection.update_one(
                    {"vector_id": vector_id},
                    {"$set": document}
                )
                logger.info(f"Updated vector: {vector_id}")
            else:
                # Insert new vector
                await vector_collection.insert_one(document)
                logger.info(f"Stored vector: {vector_id}")
            
            return True
        except Exception as e:
            logger.error(f"Error storing vector {vector_id}: {str(e)}")
            return False
    
    @staticmethod
    async def delete_embedding(vector_id: str):
        """Delete a vector embedding from MongoDB."""
        try:
            vector_collection = get_vector_collection()
            
            result = await vector_collection.delete_one({"vector_id": vector_id})
            
            if result.deleted_count > 0:
                logger.info(f"Deleted vector: {vector_id}")
                return True
            else:
                logger.warning(f"Vector not found: {vector_id}")
                return False
        except Exception as e:
            logger.error(f"Error deleting vector {vector_id}: {str(e)}")
            return False
    
    @staticmethod
    async def cosine_similarity(vec1, vec2):
        """Calculate cosine similarity between two vectors."""
        # Convert lists to numpy arrays
        vec1 = np.array(vec1)
        vec2 = np.array(vec2)
        
        # Calculate dot product
        dot_product = np.dot(vec1, vec2)
        
        # Calculate magnitudes
        magnitude1 = np.linalg.norm(vec1)
        magnitude2 = np.linalg.norm(vec2)
        
        # Calculate cosine similarity
        if magnitude1 == 0 or magnitude2 == 0:
            return 0
        else:
            return dot_product / (magnitude1 * magnitude2)
    
    @staticmethod
    async def query_embeddings(query_vector: List[float], top_k: int = 10, filter_type: str = None):
        """Query for similar vectors in MongoDB based on cosine similarity."""
        try:
            vector_collection = get_vector_collection()
            
            # Get all vectors (potentially filtered by type)
            query = {}
            if filter_type:
                query["type"] = filter_type
                
            # Note: In a production environment, you might want to limit this
            # or implement a more efficient vector search algorithm
            all_vectors = await vector_collection.find(query).to_list(10000)
            
            # Calculate similarities
            similarities = []
            for doc in all_vectors:
                similarity = await MongoDBVectorStore.cosine_similarity(query_vector, doc["vector"])
                similarities.append((doc, similarity))
            
            # Sort by similarity (descending)
            similarities.sort(key=lambda x: x[1], reverse=True)
            
            # Take top k
            top_results = similarities[:top_k]
            
            # Format results
            results = []
            for doc, score in top_results:
                results.append({
                    "id": doc["vector_id"],
                    "score": float(score),
                    "metadata": doc["metadata"]
                })
            
            return {"matches": results}
        except Exception as e:
            logger.error(f"Error querying embeddings: {str(e)}")
            return {"matches": []}