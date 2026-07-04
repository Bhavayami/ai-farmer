import json
from pydantic import BaseModel, Field
from agents.base_agent import BaseFarmerAgent
from tools.mcp_clients import MCPClient

# Input Schema
class MarketInputSchema(BaseModel):
    crop_type: str = Field(..., description="Crop to sell")
    region: str = Field(..., description="Farmer's regional marketplace context")

# Tool Definition
def get_mandi_prices(crop_type: str, region: str) -> str:
    """
    Tool that calls the market price MCP service to retrieve current mandi rates and trend indicators.
    """
    try:
        data = MCPClient.get_market_prices(crop_type, region)
        return json.dumps(data)
    except Exception as e:
        return json.dumps({"error": str(e)})

class MarketIntelligenceAgent(BaseFarmerAgent):
    """
    Agent specialized in parsing commodity price feeds, forecasting price peaks/troughs, 
    and recommending storage vs. selling decisions.
    """
    def __init__(self):
        instruction = (
            "You are a Commodity Market Analyst and Agricultural Economist. Use the tool `get_mandi_prices` "
            "to fetch the latest price rates for the specified crop in the farmer's region. Recommmend: \n"
            "1. Current market rate analysis (minimum, maximum, average mandi price per quintal).\n"
            "2. Price trend analysis (whether rising, falling, or stable compared to recent weeks).\n"
            "3. Storage recommendation: Advise whether to sell immediately or store the crop "
            "expecting a price spike in the coming 4-8 weeks.\n"
            "4. Alternative channels (e.g., e-NAM portals, contract farming, direct-to-retail options)."
        )
        super().__init__(
            name="MarketIntelligenceAgent",
            instruction=instruction,
            tools=[get_mandi_prices],
            input_schema=MarketInputSchema,
            use_pro_model=False
        )
