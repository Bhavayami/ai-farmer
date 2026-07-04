from pydantic import BaseModel, Field
from agents.base_agent import BaseFarmerAgent

class FertilizerInputSchema(BaseModel):
    crop_type: str = Field(..., description="Target crop for fertilization")
    soil_ph: float = Field(..., description="Soil pH value")
    soil_nitrogen: float = Field(..., description="Nitrogen content (mg/kg)")
    soil_phosphorus: float = Field(..., description="Phosphorus content (mg/kg)")
    soil_potassium: float = Field(..., description="Potassium content (mg/kg)")
    target_yield_tons: float = Field(default=2.5, description="Expected target yield per acre")

class FertilizerRecommendationAgent(BaseFarmerAgent):
    """
    Agent specialized in calculating exact fertilizer requirements, diagnosing 
    macronutrient deficiencies, and recommending organic/chemical balance.
    """
    def __init__(self):
        instruction = (
            "You are a Soil Scientist and Plant Nutrition expert. Analyze the crop type, target yield, "
            "and soil N-P-K levels to provide a specific fertilization prescription. Recommend: \n"
            "1. Nitrogen, Phosphorus, Potassium deficiency assessment.\n"
            "2. Specific fertilizer recommendations (e.g., Urea, DAP, MOP dosages in kg per acre).\n"
            "3. Timing and application method (basal dose, top dressing) based on crop vegetative stages.\n"
            "4. Organic soil-building recommendations (compost, biofertilizers) to match chemical inputs."
        )
        super().__init__(
            name="FertilizerRecommendationAgent",
            instruction=instruction,
            tools=[],
            input_schema=FertilizerInputSchema,
            use_pro_model=False
        )
