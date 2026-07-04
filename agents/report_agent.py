import os
from pydantic import BaseModel, Field
from agents.base_agent import BaseFarmerAgent
from tools.pdf_generator import PDFReportGenerator
from logger import logger

# Input Schema
class ReportInputSchema(BaseModel):
    farmer_name: str = Field(..., description="Farmer's name")
    region: str = Field(..., description="Farmer's region")
    crop_plan: str = Field(..., description="Crop planning advice text")
    weather_summary: str = Field(..., description="Weather intelligence advice text")
    soil_analysis: str = Field(..., description="Soil and fertilizer recommendation text")
    pest_disease_advisory: str = Field(..., description="Pest & disease advice text")
    financial_plan: str = Field(..., description="Financial planning advice text")
    gov_schemes: str = Field(..., description="Government schemes advice text")
    action_plan: str = Field(..., description="Weekly action plan advisory text")

# Tool Definition
def build_pdf_document(
    farmer_name: str,
    region: str,
    crop_plan: str,
    weather_summary: str,
    soil_analysis: str,
    pest_disease_advisory: str,
    financial_plan: str,
    gov_schemes: str,
    action_plan: str
) -> str:
    """
    Tool that generates the physical PDF document in the workspace scratch directory
    and returns its file path.
    """
    try:
        # Create scratch directory if missing
        scratch_dir = "scratch"
        if not os.path.exists(scratch_dir):
            os.makedirs(scratch_dir)
            
        safe_name = farmer_name.replace(" ", "_").lower()
        filepath = os.path.join(scratch_dir, f"advisory_{safe_name}.pdf")
        
        pdf_path = PDFReportGenerator.generate_report(
            filename=filepath,
            farmer_name=farmer_name,
            region=region,
            crop_plan=crop_plan,
            weather_summary=weather_summary,
            soil_analysis=soil_analysis,
            pest_disease_advisory=pest_disease_advisory,
            financial_plan=financial_plan,
            gov_schemes=gov_schemes,
            action_plan=action_plan
        )
        return pdf_path
    except Exception as e:
        logger.error(f"Error in build_pdf_document tool: {e}")
        return f"Error: {str(e)}"

class ReportGeneratorAgent(BaseFarmerAgent):
    """
    Agent specialized in parsing aggregate text recommendations from all sub-agents 
    and compiling them into a high-quality PDF report for local downloading.
    """
    def __init__(self):
        instruction = (
            "You are a Technical Document Compiler. Use the tool `build_pdf_document` to build the physical PDF. "
            "Write a report summary in your recommendation field, and supply the absolute file path of the "
            "generated PDF in the sources list."
        )
        super().__init__(
            name="ReportGeneratorAgent",
            instruction=instruction,
            tools=[build_pdf_document],
            input_schema=ReportInputSchema,
            use_pro_model=False
        )
