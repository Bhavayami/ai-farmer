import json
from pydantic import BaseModel, Field
from agents.base_agent import BaseFarmerAgent
from tools.mcp_clients import MCPClient

# Input Schema
class ResourceInputSchema(BaseModel):
    latitude: float = Field(..., description="Latitude coordinate")
    longitude: float = Field(..., description="Longitude coordinate")
    resource_type: str = Field(..., description="Category of resource to find (e.g., cold storage, seed store, lab)")

# Tool Definition
def search_local_mcp_places(latitude: float, longitude: float, resource_type: str) -> str:
    """
    Tool that calls the place search MCP service to look up physical agricultural suppliers, warehouses, and labs.
    """
    try:
        places = MCPClient.search_nearby_resources(latitude, longitude, resource_type)
        return json.dumps(places)
    except Exception as e:
        return json.dumps({"error": str(e)})

class MapsResourceAgent(BaseFarmerAgent):
    """
    Agent specialized in location services, routing, and cataloging nearby 
    physical farming support assets (seed dealers, cold storages, testing labs).
    """
    def __init__(self):
        instruction = (
            "You are a GIS and Agrarian Logistics Coordinator. Use the tool `search_local_mcp_places` "
            "to find nearby facilities matching the requested resource type around the coordinates. Recommend: \n"
            "1. List of matching facilities with name, estimated distance, phone, and ratings.\n"
            "2. Logistics planning suggestions (e.g. storage facilities close to highways, labs for quick soil reports).\n"
            "3. Coordination tips for hiring shared rental machinery or combining transport costs."
        )
        super().__init__(
            name="MapsResourceAgent",
            instruction=instruction,
            tools=[search_local_mcp_places],
            input_schema=ResourceInputSchema,
            use_pro_model=False
        )
