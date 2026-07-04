from pydantic import BaseModel, Field
from agents.base_agent import BaseFarmerAgent

class CropInputSchema(BaseModel):
    farmer_name: str = Field(..., description="Name of the farmer")
    region: str = Field(..., description="Geographical farming region")
    soil_ph: float = Field(..., description="Soil pH value")
    soil_nitrogen: float = Field(..., description="Soil Nitrogen level in mg/kg")
    soil_phosphorus: float = Field(..., description="Soil Phosphorus level in mg/kg")
    soil_potassium: float = Field(..., description="Soil Potassium level in mg/kg")
    soil_moisture: float = Field(..., description="Soil moisture percentage")
    farm_size_acres: float = Field(..., description="Total farm area in acres")

class CropAdvisorAgent(BaseFarmerAgent):
    """
    Agent specialized in selecting crop varieties, planting schedules, 
    and detailing optimal crop rotation sequences.
    """
    def __init__(self):
        instruction = (
            "You are a Senior Agronomist and Crop Planner. Your job is to analyze the farmer's region, "
            "farm size, and detailed N-P-K soil metrics to recommend: \n"
            "1. Three highly suitable crops (primary, secondary, cover crop).\n"
            "2. The optimal planting timeline based on regional cycles.\n"
            "3. A sustainable 3-year crop rotation sequence to maintain soil health.\n\n"
            "Keep recommendations practical, specific, and tailored to the N-P-K values provided."
        )
        super().__init__(
            name="CropAdvisorAgent",
            instruction=instruction,
            tools=[],
            input_schema=CropInputSchema,
            use_pro_model=False
        )
