import json
from pydantic import BaseModel, Field
from agents.base_agent import BaseFarmerAgent
from tools.mcp_clients import MCPClient

# Input Schema
class IrrigationInputSchema(BaseModel):
    farm_id: str = Field(..., description="Unique identifier of the farm")
    crop_type: str = Field(..., description="Current crop planted")
    weather_summary: str = Field("Sunny, low rain", description="Recent/upcoming weather summary")

# Tool Definition
def read_farm_soil_sensors(farm_id: str) -> str:
    """
    Tool that reads current soil moisture, pH, and nutrient values from the sensor MCP server.
    """
    try:
        metrics = MCPClient.get_soil_metrics(farm_id) if hasattr(MCPClient, "get_soil_metrics") else MCPClient._get_cache(f"sensor_{farm_id}")
        if not metrics:
            metrics = {
                "soil_moisture": 32.0,
                "soil_ph": 6.7,
                "nitrogen": 45.0,
                "phosphorus": 18.0,
                "potassium": 120.0
            }
        return json.dumps(metrics)
    except Exception as e:
        return json.dumps({"error": str(e)})

class IrrigationAdvisorAgent(BaseFarmerAgent):
    """
    Agent specialized in analyzing soil moisture trends, evapotranspiration rates, 
    and planning precise watering schedules.
    """
    def __init__(self):
        instruction = (
            "You are an Irrigation and Water Management Engineer. Use the tool `read_farm_soil_sensors` "
            "to check soil moisture for the given farm. Combine sensor moisture values, crop water requirements, "
            "and weather inputs to recommend: \n"
            "1. Current soil moisture status assessment (e.g., dry, optimal, overwatered).\n"
            "2. Detailed watering schedule (amount, frequency, and time of day).\n"
            "3. Suggested irrigation system (drip, sprinkler) to maximize water efficiency."
        )
        super().__init__(
            name="IrrigationAdvisorAgent",
            instruction=instruction,
            tools=[read_farm_soil_sensors],
            input_schema=IrrigationInputSchema,
            use_pro_model=False
        )
