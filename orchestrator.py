import asyncio
import json
import uuid
from typing import Dict, Any, List, Optional
import google.generativeai as genai
from config import settings
from logger import logger
from exceptions import OrchestrationException, AgentException
from memory import MemoryService

# Import specialized agents
from agents.crop_agent import CropAdvisorAgent
from agents.disease_agent import DiseaseDetectionAgent
from agents.weather_agent import WeatherIntelligenceAgent
from agents.irrigation_agent import IrrigationAdvisorAgent
from agents.fertilizer_agent import FertilizerRecommendationAgent
from agents.pest_agent import PestManagementAgent
from agents.market_agent import MarketIntelligenceAgent
from agents.gov_scheme_agent import GovernmentSchemeAgent
from agents.financial_agent import FinancialPlanningAgent
from agents.resource_agent import MapsResourceAgent
from agents.report_agent import ReportGeneratorAgent
from agents.reflection_agent import ReflectionAgent
from agents.memory_agent import MemoryManagerAgent

class AgriculturalOrchestrator:
    """
    Main Multi-Agent Orchestrator. Parses user intent, schedules specialized agents,
    runs independent sub-tasks concurrently, runs reflection audits, and manages trace logging.
    """
    def __init__(self):
        # Initialize sub-agents
        self.crop_agent = CropAdvisorAgent()
        self.disease_agent = DiseaseDetectionAgent()
        self.weather_agent = WeatherIntelligenceAgent()
        self.irrigation_agent = IrrigationAdvisorAgent()
        self.fertilizer_agent = FertilizerRecommendationAgent()
        self.pest_agent = PestManagementAgent()
        self.market_agent = MarketIntelligenceAgent()
        self.gov_scheme_agent = GovernmentSchemeAgent()
        self.financial_agent = FinancialPlanningAgent()
        self.resource_agent = MapsResourceAgent()
        self.report_agent = ReportGeneratorAgent()
        self.reflection_agent = ReflectionAgent()
        self.memory_agent = MemoryManagerAgent()
        
        self.agent_map = {
            "crop": self.crop_agent,
            "disease": self.disease_agent,
            "weather": self.weather_agent,
            "irrigation": self.irrigation_agent,
            "fertilizer": self.fertilizer_agent,
            "pest": self.pest_agent,
            "market": self.market_agent,
            "gov_scheme": self.gov_scheme_agent,
            "financial": self.financial_agent,
            "resource": self.resource_agent,
            "report": self.report_agent
        }

    async def determine_plan(self, query: str) -> List[str]:
        """
        Analyses user query and determines which agents should execute.
        Returns a list of agent keys (e.g. ["crop", "weather"]).
        """
        api_key = settings.gemini_api_key
        if not api_key or api_key == "mock_key" or "mock" in api_key:
            # Fallback local router heuristic if no API key
            logger.info("Using local heuristic router fallback")
            q_lower = query.lower()
            plan = []
            if "crop" in q_lower or "plant" in q_lower or "seed" in q_lower:
                plan.append("crop")
            if "weather" in q_lower or "rain" in q_lower or "climate" in q_lower or "temp" in q_lower:
                plan.append("weather")
            if "water" in q_lower or "irrigation" in q_lower or "moisture" in q_lower:
                plan.append("irrigation")
            if "fertilizer" in q_lower or "npk" in q_lower or "nitrogen" in q_lower:
                plan.append("fertilizer")
            if "pest" in q_lower or "bug" in q_lower or "insects" in q_lower:
                plan.append("pest")
            if "price" in q_lower or "market" in q_lower or "sell" in q_lower or "mandi" in q_lower:
                plan.append("market")
            if "scheme" in q_lower or "subsidy" in q_lower or "government" in q_lower:
                plan.append("gov_scheme")
            if "finance" in q_lower or "cost" in q_lower or "roi" in q_lower or "budget" in q_lower:
                plan.append("financial")
            if "near" in q_lower or "store" in q_lower or "map" in q_lower or "find" in q_lower:
                plan.append("resource")
            if "disease" in q_lower or "leaf" in q_lower or "spot" in q_lower or "image" in q_lower:
                plan.append("disease")
                
            # default fallback if nothing matched
            if not plan:
                plan = ["crop", "weather"]
            return list(set(plan))

        try:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel(settings.gemini_model_flash)
            
            prompt = (
                f"You are the Planning module of a Multi-Agent Farming Assistant. Given the user's query: '{query}', "
                f"determine which specialized agents from the list below are required to provide a complete answer.\n"
                f"Available agents: crop, disease, weather, irrigation, fertilizer, pest, market, gov_scheme, financial, resource, report.\n\n"
                f"Output strictly a JSON list containing the exact agent names, e.g., ['crop', 'fertilizer']. Do not include markdown wraps."
            )
            
            response = model.generate_content(prompt)
            text = response.text.strip()
            if text.startswith("```json"):
                text = text[7:]
            if text.endswith("```"):
                text = text[:-3]
            plan = json.loads(text.strip())
            if isinstance(plan, list):
                # filter invalid names
                return [a for a in plan if a in self.agent_map]
            return ["crop", "weather"]
        except Exception as e:
            logger.error(f"Failed to dynamically route query, falling back: {e}")
            return ["crop", "weather"]

    async def execute_plan(
        self,
        session_id: str,
        farmer_id: int,
        query: str,
        image_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Executes memory manager, triggers sub-agents concurrently, runs reflection,
        logs trace data, and returns the unified answer.
        """
        logger.info(f"Starting orchestration pipeline for session: {session_id}, query: {query}")
        
        # 1. Fetch Digital Farmer Profile and Historical Context (Memory Manager)
        personalized_context = await self.memory_agent.get_personalized_context(farmer_id, query)
        profile = MemoryService.get_farmer_profile(farmer_id)
        
        # 2. Determine execution plan
        plan = await self.determine_plan(query)
        logger.info(f"Dynamic execution plan generated: {plan}")
        
        # Assemble inputs for sub-agents
        agent_inputs = {
            "crop": {
                "farmer_name": profile.get("name", "Farmer"),
                "region": profile.get("region", "India"),
                "soil_ph": profile.get("soil_ph", 6.5),
                "soil_nitrogen": profile.get("soil_nitrogen", 45.0),
                "soil_phosphorus": profile.get("soil_phosphorus", 18.0),
                "soil_potassium": profile.get("soil_potassium", 120.0),
                "soil_moisture": profile.get("soil_moisture", 30.0),
                "farm_size_acres": profile.get("farm_size_acres", 5.0)
            },
            "disease": {
                "image_path": image_path or "",
                "crop_context": ", ".join(profile.get("primary_crops", ["Unknown"]))
            },
            "weather": {
                "latitude": profile.get("latitude", 19.076),
                "longitude": profile.get("longitude", 72.877),
                "days_forecast": 7
            },
            "irrigation": {
                "farm_id": f"farm_{farmer_id}",
                "crop_type": profile.get("primary_crops", ["Rice"])[0],
                "weather_summary": "Upcoming moderate rainfall expected."
            },
            "fertilizer": {
                "crop_type": profile.get("primary_crops", ["Rice"])[0],
                "soil_ph": profile.get("soil_ph", 6.5),
                "soil_nitrogen": profile.get("soil_nitrogen", 45.0),
                "soil_phosphorus": profile.get("soil_phosphorus", 18.0),
                "soil_potassium": profile.get("soil_potassium", 120.0)
            },
            "pest": {
                "crop_type": profile.get("primary_crops", ["Rice"])[0],
                "weather_summary": "High humidity, average temp 29 degrees.",
                "observed_pests": "None"
            },
            "market": {
                "crop_type": profile.get("primary_crops", ["Rice"])[0],
                "region": profile.get("region", "Maharashtra")
            },
            "gov_scheme": {
                "region": profile.get("region", "Maharashtra"),
                "crop_type": profile.get("primary_crops", ["Rice"])[0],
                "farm_size_acres": profile.get("farm_size_acres", 5.0)
            },
            "financial": {
                "crop_type": profile.get("primary_crops", ["Rice"])[0],
                "farm_size_acres": profile.get("farm_size_acres", 5.0),
                "estimated_mandi_price": 2200.0,
                "expected_yield_quintals_per_acre": 14.5
            },
            "resource": {
                "latitude": profile.get("latitude", 19.076),
                "longitude": profile.get("longitude", 72.877),
                "resource_type": "seed store"
            }
        }
        
        # Override specific inputs based on query content
        if "disease" in plan and not image_path:
            # If disease is requested but no image exists, fail gracefully
            plan.remove("disease")
            logger.warning("Disease agent requested but no image provided. Skipping.")

        # 3. Concurrent sub-agent execution
        tasks = []
        active_agents = []
        
        for agent_key in plan:
            agent = self.agent_map.get(agent_key)
            inputs = agent_inputs.get(agent_key, {})
            # Add general personalized context to inputs
            inputs["personalized_history"] = personalized_context
            
            # Create a task for agent execution
            tasks.append(agent.execute(
                user_id=f"user_{farmer_id}",
                session_id=session_id,
                inputs=inputs
            ))
            active_agents.append(agent_key)
            
        logger.info(f"Triggering concurrent execution for agents: {active_agents}")
        
        # Run sub-agents concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        sub_agent_reports = {}
        execution_trace = {}
        
        for agent_key, res in zip(active_agents, results):
            if isinstance(res, Exception):
                logger.error(f"Sub-agent '{agent_key}' execution failed with: {res}")
                execution_trace[agent_key] = {
                    "status": "FAILED",
                    "error": str(res)
                }
            else:
                sub_agent_reports[agent_key] = res
                execution_trace[agent_key] = {
                    "status": "SUCCESS",
                    "confidence": res.confidence_score,
                    "reasoning": res.reasoning_trace,
                    "sources": res.sources,
                    "content": res.recommendation
                }
                
        # 4. Aggregation of sub-agent recommendations
        aggregated_text = ""
        for agent_key, report in sub_agent_reports.items():
            aggregated_text += f"\n--- {agent_key.upper()} ADVISORY ---\n"
            aggregated_text += f"Confidence Score: {report.confidence_score}\n"
            aggregated_text += f"Recommendation: {report.recommendation}\n"
            aggregated_text += f"Sources: {', '.join(report.sources)}\n"
            
        # 5. Reflection Audit (Reflection Agent)
        logger.info("Initiating Reflection Audit on aggregated sub-agent findings.")
        try:
            reflection_res = await self.reflection_agent.execute(
                user_id=f"user_{farmer_id}",
                session_id=session_id,
                inputs={
                    "farmer_query": query,
                    "aggregated_recommendations": aggregated_text
                }
            )
            final_advisory = reflection_res.recommendation
            reflection_trace = {
                "confidence": reflection_res.confidence_score,
                "reasoning": reflection_res.reasoning_trace,
                "sources": reflection_res.sources
            }
        except Exception as e:
            logger.error(f"Reflection Agent failed: {e}. Falling back to direct aggregated advice.")
            final_advisory = aggregated_text
            reflection_trace = {"status": "FAILED", "error": str(e)}

        # 6. Check if PDF compile is needed
        pdf_path = None
        if "report" in query.lower() or "pdf" in query.lower():
            logger.info("PDF Generation requested. Triggering Report Generator Agent.")
            try:
                report_inputs = {
                    "farmer_name": profile.get("name", "Farmer"),
                    "region": profile.get("region", "India"),
                    "crop_plan": sub_agent_reports.get("crop", getattr(self.crop_agent, "recommendation", "Not requested.")).recommendation if "crop" in sub_agent_reports else "Not requested.",
                    "weather_summary": sub_agent_reports.get("weather", "").recommendation if "weather" in sub_agent_reports else "Not requested.",
                    "soil_analysis": sub_agent_reports.get("fertilizer", "").recommendation if "fertilizer" in sub_agent_reports else "Not requested.",
                    "pest_disease_advisory": sub_agent_reports.get("disease", "").recommendation if "disease" in sub_agent_reports else "Not requested.",
                    "financial_plan": sub_agent_reports.get("financial", "").recommendation if "financial" in sub_agent_reports else "Not requested.",
                    "gov_schemes": sub_agent_reports.get("gov_scheme", "").recommendation if "gov_scheme" in sub_agent_reports else "Not requested.",
                    "action_plan": final_advisory
                }
                report_res = await self.report_agent.execute(
                    user_id=f"user_{farmer_id}",
                    session_id=session_id,
                    inputs=report_inputs
                )
                if report_res.sources:
                    pdf_path = report_res.sources[0]
            except Exception as e:
                logger.error(f"Report compile failed: {e}")

        # 7. Persistent Logging to database (Explainability Trace)
        topic = "General Consultation"
        if "disease" in plan:
            topic = "Disease Diagnosis"
        elif "crop" in plan:
            topic = "Crop Planning"
            
        trace_data = {
            "agents_called": active_agents,
            "agent_details": execution_trace,
            "reflection": reflection_trace
        }
        
        MemoryService.log_recommendation(
            session_id=session_id,
            topic=topic,
            query=query,
            trace=trace_data,
            recommendation=final_advisory,
            farmer_id=farmer_id
        )
        
        # 8. Update Session Conversation Memory
        MemoryService.add_message(session_id, "user", query, farmer_id)
        MemoryService.add_message(session_id, "assistant", final_advisory, farmer_id)
        
        return {
            "final_advisory": final_advisory,
            "execution_trace": trace_data,
            "pdf_path": pdf_path
        }
