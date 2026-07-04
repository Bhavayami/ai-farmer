from pydantic import BaseModel, Field
from agents.base_agent import BaseFarmerAgent

class FinancialInputSchema(BaseModel):
    crop_type: str = Field(..., description="Selected crop")
    farm_size_acres: float = Field(..., description="Land size in acres")
    estimated_mandi_price: float = Field(..., description="Current mandi price per quintal in INR")
    expected_yield_quintals_per_acre: float = Field(default=15.0, description="Expected yield per acre")

class FinancialPlanningAgent(BaseFarmerAgent):
    """
    Agent specialized in cost-of-cultivation estimates, budgeting, cash flow forecasting, 
    and return on investment (ROI) calculations.
    """
    def __init__(self):
        instruction = (
            "You are a Micro-Finance and Farm Management Consultant. Analyze the crop type, farm size, "
            "expected yield, and current market price to build a detailed crop budget. Outline: \n"
            "1. Estimated Cost of Cultivation (seeds, labor, fertilizer, tillage, irrigation) per acre.\n"
            "2. Expected gross revenue (total yield x market price).\n"
            "3. Net profit margins and return on investment (ROI) percentage.\n"
            "4. Risk mitigation suggestions (e.g. diversified cropping, credit allocation) to avoid debt traps."
        )
        super().__init__(
            name="FinancialPlanningAgent",
            instruction=instruction,
            tools=[],
            input_schema=FinancialInputSchema,
            use_pro_model=False
        )
