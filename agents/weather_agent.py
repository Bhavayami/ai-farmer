import json
from pydantic import BaseModel, Field
from agents.base_agent import BaseFarmerAgent
from tools.mcp_clients import MCPClient

# Input Schema
class WeatherInputSchema(BaseModel):
    latitude: float = Field(..., description="Latitude of the farm")
    longitude: float = Field(..., description="Longitude of the farm")
    days_forecast: int = Field(7, description="Number of days to forecast")

# Tool Definition
def get_weather_report(latitude: float, longitude: float) -> str:
    """
    Tool that calls the weather MCP service to fetch forecast data for a coordinate.
    """
    try:
        data = MCPClient.get_weather_data(latitude, longitude)
        return json.dumps(data)
    except Exception as e:
        return json.dumps({"error": str(e)})

class WeatherIntelligenceAgent(BaseFarmerAgent):
    """
    Agent specialized in parsing multi-day weather forecasts and issuing warnings for 
    frost, rain during harvest, or heatwaves, as well as calculating optimal pesticide spraying windows.
    """
    def __init__(self):
        instruction = (
            "You are an Agricultural Meteorologist. Use the tool `get_weather_report` to analyze the "
            "forecast for the farmer's coordinates. Your response should outline: \n"
            "1. Current conditions (temp, humidity, wind).\n"
            "2. 7-day outlook highlighting risks (e.g., heavy rain, high heat, frost).\n"
            "3. Actionable spraying/fertilization advice (e.g., do not spray if wind > 15 km/h or rain probability > 60%)."
        )
        super().__init__(
            name="WeatherIntelligenceAgent",
            instruction=instruction,
            tools=[get_weather_report],
            input_schema=WeatherInputSchema,
            use_pro_model=False
        )
