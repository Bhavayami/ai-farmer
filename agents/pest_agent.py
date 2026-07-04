from pydantic import BaseModel, Field
from agents.base_agent import BaseFarmerAgent

class PestInputSchema(BaseModel):
    crop_type: str = Field(..., description="Type of crop under threat")
    weather_summary: str = Field(..., description="Recent weather data (humidity, temperature)")
    observed_pests: str = Field("None", description="Any pests currently spotted by the farmer")

class PestManagementAgent(BaseFarmerAgent):
    """
    Agent specialized in Integrated Pest Management (IPM), biological pest controls, 
    and safe pesticide usage instructions.
    """
    def __init__(self):
        instruction = (
            "You are an Agricultural Entomologist and Crop Protection Expert. "
            "Analyze the crop type, weather patterns (high humidity often raises fungal/pest risks), "
            "and observed pests to recommend: \n"
            "1. Major pest risks for this crop in current weather conditions.\n"
            "2. Biological/organic management methods (e.g., pheromone traps, neem spray, ladybugs).\n"
            "3. Target chemical pesticides (including dosages and safety intervals) if infestation occurs.\n"
            "4. Safety guidelines for spray operators (masks, wind direction, water volume)."
        )
        super().__init__(
            name="PestManagementAgent",
            instruction=instruction,
            tools=[],
            input_schema=PestInputSchema,
            use_pro_model=False
        )
