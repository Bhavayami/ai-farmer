import json
from pydantic import BaseModel, Field
from agents.base_agent import BaseFarmerAgent
from tools.mcp_clients import MCPClient

# Input Schema
class GovSchemeInputSchema(BaseModel):
    region: str = Field(..., description="Farmer's home state or region")
    crop_type: str = Field(..., description="Crops under cultivation")
    farm_size_acres: float = Field(..., description="Farm size in acres")

# Tool Definition
def search_agricultural_schemes(query: str) -> str:
    """
    Tool that searches federal and state databases for government schemes, subsidies, and insurances.
    """
    try:
        content = MCPClient.search_web(query)
        return content
    except Exception as e:
        return f"Error conducting search: {str(e)}"

class GovernmentSchemeAgent(BaseFarmerAgent):
    """
    Agent specialized in identifying federal and state-level agricultural subsidies, 
    crop insurance benefits, and credit schemes (like Kisan Credit Card).
    """
    def __init__(self):
        instruction = (
            "You are a Public Policy and Rural Development Expert. Use the tool `search_agricultural_schemes` "
            "to check for relevant schemes for the farmer's crops, region, and land size. Recommend: \n"
            "1. Three critical government schemes the farmer is eligible for (e.g., PM-KISAN, PMFBY, KCC, soil health cards).\n"
            "2. Details on subsidies for irrigation, solar pumps, organic seeds, or heavy machinery.\n"
            "3. Step-by-step instructions on where and how to apply, including required documents."
        )
        super().__init__(
            name="GovernmentSchemeAgent",
            instruction=instruction,
            tools=[search_agricultural_schemes],
            input_schema=GovSchemeInputSchema,
            use_pro_model=False
        )
