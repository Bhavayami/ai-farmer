import json
import os
from PIL import Image
from pydantic import BaseModel, Field
from agents.base_agent import BaseFarmerAgent
from config import settings
from logger import logger

# Input Schema
class DiseaseInputSchema(BaseModel):
    image_path: str = Field(..., description="Absolute path to the uploaded leaf or plant image")
    crop_context: str = Field("Unknown", description="Type of crop being inspected")

# Multimodal Tool Definition
def analyze_leaf_image(image_path: str) -> str:
    """
    Tool that opens an image file and sends it to Gemini 2.5 Pro Vision
    for disease identification and diagnostic assessment.
    """
    if not os.path.exists(image_path):
        return json.dumps({"error": f"Image file not found at: {image_path}"})
        
    try:
        # Check API Key validity
        api_key = settings.gemini_api_key
        if not api_key or api_key == "mock_key" or "mock" in api_key:
            logger.info("Using mock diagnosis due to missing or invalid Gemini API Key.")
            return json.dumps({
                "diagnosis": "Tomato Early Blight (Alternaria solani)",
                "confidence": 0.88,
                "symptoms": [
                    "Concentric ring spots (target board effect) on older leaves.",
                    "Yellow halos surrounding the necrotic lesions.",
                    "Premature defoliation of lower canopy leaves."
                ],
                "treatment_organic": "Apply neem oil sprays weekly and prune lower leaves to improve air circulation.",
                "treatment_chemical": "Spray chlorothalonil or copper-based fungicide at 7-10 day intervals."
            })
            
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        
        # Load image using PIL
        img = Image.open(image_path)
        
        # Configure model
        model = genai.GenerativeModel(settings.gemini_model_pro)
        prompt = (
            "Analyze this crop/plant image carefully. Determine if the plant is healthy or infected with a disease or pest. "
            "Output your findings in structured JSON format with the following keys:\n"
            "- diagnosis: The identified disease name or issue\n"
            "- confidence: A score between 0.0 and 1.0\n"
            "- symptoms: A list of visual symptoms identified in the photo\n"
            "- treatment_organic: Organic control recommendations\n"
            "- treatment_chemical: Chemical control recommendations"
        )
        
        response = model.generate_content([prompt, img])
        return response.text.strip()
    except Exception as e:
        logger.error(f"Error executing analyze_leaf_image tool: {e}")
        return json.dumps({"error": f"Failed to process image: {str(e)}"})

class DiseaseDetectionAgent(BaseFarmerAgent):
    """
    Agent utilizing Gemini Vision capabilities to diagnose crop leaf infections 
    and output actionable treatment pathways.
    """
    def __init__(self):
        instruction = (
            "You are a Plant Pathologist and crop doctor. Your goal is to inspect crop images using the "
            "provided tool `analyze_leaf_image` to diagnose infections. \n"
            "Analyze the tool response, explain the symptoms clearly to the farmer, and list both organic "
            "and chemical remediation paths."
        )
        super().__init__(
            name="DiseaseDetectionAgent",
            instruction=instruction,
            tools=[analyze_leaf_image],
            input_schema=DiseaseInputSchema,
            use_pro_model=True  # Vision uses Pro
        )
