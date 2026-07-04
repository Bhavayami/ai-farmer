from pydantic import BaseModel, Field
from agents.base_agent import BaseFarmerAgent
from memory import MemoryService

class MemoryInputSchema(BaseModel):
    farmer_id: int = Field(..., description="ID of the farmer")
    user_query: str = Field(..., description="The incoming user query")

class MemoryManagerAgent(BaseFarmerAgent):
    """
    Agent specialized in fetching relevant long-term farmer context, analyzing 
    soil history, and summarizing changes in the Digital Farmer Profile over time.
    """
    def __init__(self):
        instruction = (
            "You are a Farming History and Memory Auditor. Your goal is to review the farmer's historical context "
            "and suggest how current recommendations can be customized based on past events (e.g. if a previous crop "
            "failed due to root rot, or if the farmer has a high soil-pH history). \n"
            "Return a personalized profile context block for the Orchestrator to route to sub-agents."
        )
        super().__init__(
            name="MemoryManagerAgent",
            instruction=instruction,
            tools=[],
            input_schema=MemoryInputSchema,
            use_pro_model=False
        )
        
    async def get_personalized_context(self, farmer_id: int, query: str) -> str:
        """
        Custom execution helper that pulls data from the local SQLite long-term storage
        and formats it for LLM utilization.
        """
        history_text = MemoryService.retrieve_long_term_context(farmer_id, query)
        profile = MemoryService.get_farmer_profile(farmer_id)
        
        context_summary = (
            f"FARMER PROFILE SUMMARY:\n"
            f"- Farmer ID: {farmer_id}\n"
            f"- Name: {profile.get('name')}\n"
            f"- Region: {profile.get('region')}\n"
            f"- Soil N-P-K: {profile.get('soil_nitrogen')}-{profile.get('soil_phosphorus')}-{profile.get('soil_potassium')} mg/kg, pH: {profile.get('soil_ph')}\n"
            f"- Soil Moisture: {profile.get('soil_moisture')}%\n"
            f"- Primary Crops: {', '.join(profile.get('primary_crops', []))}\n\n"
            f"HISTORICAL CONTEXT FROM PAST CONSULTATIONS:\n"
            f"{history_text}"
        )
        return context_summary
