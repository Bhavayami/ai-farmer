import pytest
import asyncio
import os
import json
from datetime import datetime
from config import settings
from exceptions import ValidationException, AgentException
from database import db_manager, ChatSessionRepository, FarmerProfileRepository
from tools.mcp_clients import MCPClient
from orchestrator import AgriculturalOrchestrator
from agents.crop_agent import CropAdvisorAgent
from agents.base_agent import AgentResponse

# Ensure SQLite test database is isolated
settings.sql_database_url = "sqlite:///test_farming.db"

@pytest.fixture(scope="module")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

# 1. MCP Clients Unit Tests
def test_weather_client_mock():
    data = MCPClient.get_weather_data(19.076, 72.877)
    assert "current" in data
    assert "daily" in data
    assert len(data["daily"]) == 7
    assert data["current"]["temp"] == 30.5

def test_market_client_mock():
    data = MCPClient.get_market_prices("Wheat", "Punjab")
    assert data["crop"] == "Wheat"
    assert data["currency"] == "INR"
    assert "pricing" in data
    assert data["pricing"]["current"] > 0

def test_places_client_mock():
    places = MCPClient.search_nearby_resources(19.076, 72.877, "seed store")
    assert len(places) > 0
    assert any("seed" in p["type"] or "seed" in p["name"].lower() for p in places)

# 2. Database Repository Tests
def test_save_and_get_farmer_profile():
    db = next(db_manager.get_db())
    profile_data = {
        "name": "Test Farmer",
        "region": "Test State, India",
        "latitude": 12.34,
        "longitude": 56.78,
        "farm_size_acres": 10.0,
        "soil_ph": 6.2,
        "primary_crops": "Rice"
    }
    profile = FarmerProfileRepository.save_profile(db, profile_data)
    assert profile.id is not None
    assert profile.name == "Test Farmer"
    
    fetched = FarmerProfileRepository.get_profile(db, profile.id)
    assert fetched is not None
    assert fetched.farm_size_acres == 10.0

def test_save_chat_session():
    db = next(db_manager.get_db())
    session_id = "test_session_123"
    history = [{"role": "user", "content": "Hello"}, {"role": "assistant", "content": "Hi"}]
    
    session = ChatSessionRepository.save_session(db, session_id, history)
    assert session.session_id == session_id
    assert "assistant" in session.chat_history

# 3. Agent Execution Tests (Asynchronous)
@pytest.mark.asyncio
async def test_base_agent_validation():
    agent = CropAdvisorAgent()
    # Missing required inputs should raise ValidationException
    with pytest.raises(ValidationException):
        await agent.execute("test_user", "test_sess", {"farmer_name": "Test"})

# 4. Orchestration Pipeline Test
@pytest.mark.asyncio
async def test_orchestration_routing():
    orchestrator = AgriculturalOrchestrator()
    plan = await orchestrator.determine_plan("Tell me about wheat prices and government schemes.")
    assert "market" in plan or "gov_scheme" in plan
