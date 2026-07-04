import json
import asyncio
from typing import Dict, Any, List, Optional, Type
from pydantic import BaseModel, ValidationError
from google.adk import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from config import settings
from logger import logger
from exceptions import AgentException, ValidationException

class AgentResponse(BaseModel):
    """
    Standardized, structured output for all specialized farming agents.
    Ensures confidence scoring and explainability are built-in.
    """
    recommendation: str
    confidence_score: float  # Scale of 0.0 to 1.0
    reasoning_trace: List[str]
    sources: List[str]

class BaseFarmerAgent:
    """
    Base wrapper for all AI Farmer Assistant agents.
    Integrates Google ADK Agent with validation, retries, and formatting.
    """
    def __init__(
        self,
        name: str,
        instruction: str,
        tools: List[Any] = [],
        input_schema: Type[BaseModel] = BaseModel,
        use_pro_model: bool = False
    ):
        self.name = name
        self.instruction = instruction
        self.tools = tools
        self.input_schema = input_schema
        self.model = settings.gemini_model_pro if use_pro_model else settings.gemini_model_flash
        
        # System instructions enforcing JSON format conforming to AgentResponse
        json_instruction = (
            f"{instruction}\n\n"
            "CRITICAL: You MUST respond strictly in valid JSON format matching the schema below. "
            "Do not include markdown tags like ```json or any other text before/after the JSON. "
            "Output schema:\n"
            "{\n"
            '  "recommendation": "detailed advice string",\n'
            '  "confidence_score": 0.85,\n'
            '  "reasoning_trace": ["step 1 reasoning", "step 2 reasoning"],\n'
            '  "sources": ["source 1", "source 2"]\n'
            "}"
        )
        
        # Initialize Google ADK Agent
        self.adk_agent = Agent(
            name=self.name,
            model=self.model,
            instruction=json_instruction,
            tools=self.tools
        )
        logger.info(f"Initialized Agent '{self.name}' using model '{self.model}'")

    async def execute(
        self,
        user_id: str,
        session_id: str,
        inputs: Dict[str, Any],
        session_service: Optional[Any] = None
    ) -> AgentResponse:
        """
        Executes the agent workflow with input validation, retries, and JSON parsing.
        """
        # 1. Input Validation
        try:
            if self.input_schema != BaseModel:
                self.input_schema(**inputs)
        except ValidationError as e:
            logger.error(f"[{self.name}] Input validation failed: {e}")
            raise ValidationException(f"Invalid inputs for {self.name}", {"errors": e.errors()})

        # Set up default session service if none provided
        if not session_service:
            session_service = InMemorySessionService()

        # 2. Execution with retry logic
        max_retries = 3
        backoff = 1.0
        
        prompt_str = f"Process inputs: {json.dumps(inputs)}"
        
        for attempt in range(max_retries):
            try:
                logger.info(f"[{self.name}] Execution attempt {attempt+1}/{max_retries}")
                
                # ADK Runner handles session context and tools
                runner = Runner(agent=self.adk_agent, session_service=session_service)
                final_text = ""
                
                async for event in runner.run_async(
                    user_id=user_id,
                    session_id=session_id,
                    new_message=prompt_str
                ):
                    if event.is_final_response():
                        if event.content and event.content.parts:
                            final_text += event.content.parts[0].text
                
                if not final_text:
                    raise AgentException("Empty response from LLM runner.")
                
                # 3. Clean and parse JSON response
                cleaned_text = final_text.strip()
                if cleaned_text.startswith("```json"):
                    cleaned_text = cleaned_text[7:]
                if cleaned_text.endswith("```"):
                    cleaned_text = cleaned_text[:-3]
                cleaned_text = cleaned_text.strip()
                
                parsed_json = json.loads(cleaned_text)
                
                # 4. Standardize response schema
                return AgentResponse(
                    recommendation=parsed_json.get("recommendation", ""),
                    confidence_score=float(parsed_json.get("confidence_score", 0.0)),
                    reasoning_trace=parsed_json.get("reasoning_trace", []),
                    sources=parsed_json.get("sources", [])
                )
                
            except json.JSONDecodeError as je:
                logger.warning(f"[{self.name}] JSON parse failed on attempt {attempt+1}: {je}. Response: {final_text}")
                if attempt == max_retries - 1:
                    # Fallback representation of text if JSON parse repeatedly fails
                    return AgentResponse(
                        recommendation=final_text,
                        confidence_score=0.4,
                        reasoning_trace=["Model failed to return JSON, parsed raw text."],
                        sources=["Gemini Direct Output"]
                    )
            except Exception as e:
                logger.warning(f"[{self.name}] Error on attempt {attempt+1}: {e}")
                if attempt == max_retries - 1:
                    raise AgentException(f"Agent {self.name} failed after {max_retries} attempts.", {"error": str(e)})
            
            await asyncio.sleep(backoff)
            backoff *= 2.0
            
        raise AgentException(f"Agent {self.name} failed execution.")
