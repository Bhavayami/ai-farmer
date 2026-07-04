from pydantic import BaseModel, Field
from agents.base_agent import BaseFarmerAgent

class ReflectionInputSchema(BaseModel):
    farmer_query: str = Field(..., description="The original user query")
    aggregated_recommendations: str = Field(..., description="The combined text outputs from sub-agents")

class ReflectionAgent(BaseFarmerAgent):
    """
    Agent specialized in evaluating aggregate farming recommendations for logical inconsistencies, 
    agronomic contradictions, safety warnings, and potential hallucination check.
    """
    def __init__(self):
        instruction = (
            "You are an Agronomic Quality Control and Risk Auditor. Your job is to read the combined recommendations "
            "intended for the farmer, and check for: \n"
            "1. Contradictions (e.g., advising crop watering during a rain warning, or spraying pesticide in high winds).\n"
            "2. Safety gaps (e.g., prescribing chemicals without listing personal protective equipment or harvesting intervals).\n"
            "3. Logic flaws (e.g., proposing fertilizer dosages that do not align with the N-P-K deficiency results).\n\n"
            "Rewrite the advice if necessary, adding clear, prominent safety/warning callouts where required."
        )
        super().__init__(
            name="ReflectionAgent",
            instruction=instruction,
            tools=[],
            input_schema=ReflectionInputSchema,
            use_pro_model=True  # Reflection requires high-reasoning Pro model
        )
