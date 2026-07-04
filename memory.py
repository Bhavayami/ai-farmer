import json
from typing import Dict, Any, List, Optional
from database import (
    db_manager,
    ChatSessionRepository,
    FarmerProfileRepository,
    RecommendationLogRepository
)
from logger import logger

class MemoryService:
    """
    Coordinates short-term chat logs, digital farmer profiles, and
    long-term memory summarization.
    """
    
    @staticmethod
    def get_conversation_history(session_id: str) -> List[Dict[str, Any]]:
        """
        Retrieves short-term conversation logs for the session.
        """
        db = next(db_manager.get_db())
        try:
            session = ChatSessionRepository.get_session(db, session_id)
            if session:
                return json.loads(session.chat_history)
            return []
        except Exception as e:
            logger.error(f"Error fetching conversation history: {e}")
            return []

    @staticmethod
    def add_message(session_id: str, role: str, content: str, farmer_id: Optional[int] = None):
        """
        Appends a message to short-term session storage.
        """
        db = next(db_manager.get_db())
        try:
            history = MemoryService.get_conversation_history(session_id)
            history.append({"role": role, "content": content})
            ChatSessionRepository.save_session(db, session_id, history, farmer_id)
        except Exception as e:
            logger.error(f"Error adding message to session memory: {e}")

    @staticmethod
    def get_farmer_profile(farmer_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Retrieves the Digital Farmer Profile. If farmer_id is None, returns the latest profile.
        """
        db = next(db_manager.get_db())
        try:
            if farmer_id:
                profile = FarmerProfileRepository.get_profile(db, farmer_id)
            else:
                profile = FarmerProfileRepository.get_latest_profile(db)
                
            if profile:
                return {
                    "id": profile.id,
                    "name": profile.name,
                    "region": profile.region,
                    "latitude": profile.latitude,
                    "longitude": profile.longitude,
                    "farm_size_acres": profile.farm_size_acres,
                    "soil_ph": profile.soil_ph,
                    "soil_nitrogen": profile.soil_nitrogen,
                    "soil_phosphorus": profile.soil_phosphorus,
                    "soil_potassium": profile.soil_potassium,
                    "soil_moisture": profile.soil_moisture,
                    "primary_crops": [c.strip() for c in profile.primary_crops.split(",") if c.strip()]
                }
        except Exception as e:
            logger.error(f"Error reading farmer profile: {e}")
            
        # Return default profile values
        return {
            "id": 1,
            "name": "Arjun Patel",
            "region": "Maharashtra, India",
            "latitude": 19.0760,
            "longitude": 72.8777,
            "farm_size_acres": 5.2,
            "soil_ph": 6.8,
            "soil_nitrogen": 48.0,
            "soil_phosphorus": 20.0,
            "soil_potassium": 115.0,
            "soil_moisture": 35.0,
            "primary_crops": ["Sugarcane", "Cotton"]
        }

    @staticmethod
    def save_farmer_profile(profile_data: Dict[str, Any]) -> int:
        """
        Saves or updates a farmer profile in the database.
        """
        db = next(db_manager.get_db())
        try:
            # Convert list of crops back to comma-separated string
            if "primary_crops" in profile_data and isinstance(profile_data["primary_crops"], list):
                profile_data["primary_crops"] = ", ".join(profile_data["primary_crops"])
            
            profile = FarmerProfileRepository.save_profile(db, profile_data)
            return profile.id
        except Exception as e:
            logger.error(f"Error saving farmer profile: {e}")
            return 1

    @staticmethod
    def retrieve_long_term_context(farmer_id: int, query: str) -> str:
        """
        Queries past recommendations and consultations to find relevant context.
        Uses simple keyword matching across historical recommendations for local persistence.
        """
        db = next(db_manager.get_db())
        try:
            logs = RecommendationLogRepository.get_logs_by_farmer(db, farmer_id)
            if not logs:
                return "No historical farming records found."
            
            # Simple keyword match search
            keywords = [w.lower() for w in query.split() if len(w) > 3]
            matches = []
            for log in logs:
                # Score the relevance
                score = 0
                for kw in keywords:
                    if kw in log.input_query.lower() or kw in log.final_recommendation.lower():
                        score += 1
                if score > 0:
                    matches.append((score, log))
            
            if matches:
                # Sort by score descending
                matches.sort(key=lambda x: x[0], reverse=True)
                top_logs = matches[:3]
                context_blocks = []
                for _, log in top_logs:
                    context_blocks.append(
                        f"On {log.created_at.strftime('%Y-%m-%d')}, the farmer asked about: '{log.input_query}'.\n"
                        f"Recommendation provided: {log.final_recommendation[:250]}..."
                    )
                return "\n\n".join(context_blocks)
                
            # If no matches, return a brief overview of past topics
            topics = set([log.topic for log in logs])
            return f"Farmer has {len(logs)} past logs covering topics: {', '.join(topics)}."
        except Exception as e:
            logger.error(f"Error retrieving long-term context: {e}")
            return "Unable to retrieve historical farming logs."
            
    @staticmethod
    def log_recommendation(session_id: str, topic: str, query: str, trace: Dict[str, Any], recommendation: str, farmer_id: Optional[int] = None):
        """
        Logs a generated multi-agent recommendation trace.
        """
        db = next(db_manager.get_db())
        try:
            RecommendationLogRepository.log(db, session_id, topic, query, trace, recommendation, farmer_id)
        except Exception as e:
            logger.error(f"Error logging recommendation details: {e}")
