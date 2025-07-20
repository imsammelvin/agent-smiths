from pydantic import BaseModel
from typing import Optional, Dict, Any
from pydantic_ai import Agent
import os

BASE_URL = f"http://localhost:8000/v1"

os.environ["BASE_URL"]    = BASE_URL
os.environ["OPENAI_API_KEY"] = "abc-123"   

print("Config set:", BASE_URL)

import os
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openai import OpenAIProvider

provider = OpenAIProvider(
    base_url=os.environ["BASE_URL"],
    api_key=os.environ["OPENAI_API_KEY"],
)

agent_model = model = OpenAIModel("Qwen3-30B-A3B", provider=provider)

class OptimalTime(BaseModel):
    start_time_of_meeting: Optional[str] = None  # Meeting Start
    end_time_of_meeting: Optional[str] = None    # Meeting End
    duration_minutes: Optional[int] = None  # Duration of the meeting in minutes
    metadata: Optional[str] = None # Why I Chose The Time

slots_agents = Agent(
    model,
    output_type=OptimalTime,
    system_prompt=f"""
    Available Free Slots Common Between All The Attendees Will Be Given
    Duration Of The Meeting: Will Be Given

    Return Should Have
    start_timeframe:Meeting Start Time
    end_timeframe:Meeting End Time
    duration_minutes:Duration of the meeting in minutes
    metadata:Why You Chose The Time

    Note: Meeting Start - End Time should of given duration_minutes
    
    Return the optimal meeting time that maximizes convenience for all attendees while respecting the duration requirements.
    """,
)