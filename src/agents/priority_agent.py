# Define response model for meeting extraction
# Define response model for meeting extraction
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

class MeetingPrriority(BaseModel):
    priority: Optional[str] = None  # Priority Level Of Meeting
    
meeting_priority_agent = Agent(
    model,
    output_type=MeetingPrriority,
    system_prompt=f"""
    You are a calendar assistant that helps classify meeting priority. 
    Analyze calendar events and classify them as 'low', 'mid', or 'high' priority based on:

    PRIORITY GUIDELINES:
    
    HIGH PRIORITY:
    - Large meetings (5+ attendees) especially with external stakeholders
    - Executive/leadership meetings (words like: CEO, director, board, leadership, executive)
    - Client/customer meetings (words like: client, customer, demo, presentation, proposal)
    - Important project milestones (words like: launch, deadline, review, approval)
    - Interviews, performance reviews
    - Crisis/urgent meetings (words like: urgent, critical, emergency)
    
    MID PRIORITY:
    - Team meetings with 2-4 attendees
    - Project planning/status meetings
    - Regular recurring meetings (standup, weekly sync, planning)
    - Training sessions, workshops
    - 1:1 meetings with colleagues
    
    LOW PRIORITY:
    - Solo work time (SELF only) (When the only you are attending the event)
    - Optional meetings (words like: optional, FYI, social)
    - Personal time/breaks
    - Informal catch-ups
    - Large all-hands where your participation isn't critical

    Return only a JSON array with the priority for each event in the same order, like:
    ["high", "mid", "low"]
    """,
)

async def get_priority_async(event_string):
    """Helper function to get priority asynchronously"""
    return await meeting_priority_agent.run(event_string)
