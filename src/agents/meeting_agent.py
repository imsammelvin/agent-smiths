# Define response model for meeting extraction
from pydantic import BaseModel
import os
from typing import Optional, Dict, Any
from pydantic_ai import Agent

from datetime import datetime, timezone, timedelta


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

# Define response model for meeting extraction
from pydantic import BaseModel
class MeetingTimeframe(BaseModel):
    start_timeframe: Optional[str] = None  # When to start looking for slots
    end_timeframe: Optional[str] = None    # When to stop looking for slots
    duration_minutes: Optional[int] = None  # Duration of the meeting in minutes
meeting_agent = Agent(
    model,
    output_type=MeetingTimeframe,
    system_prompt=f"""
    You are an expert at extracting meeting scheduling information from emails and messages.
    
    Current datetime: {datetime.now().strftime("%Y-%m-%dT%H:%M:%S%z")}
    Current date: {datetime.now().strftime("%A")}
    
    Your task is to analyze the content and extract meeting scheduling parameters:
    
    1. start_timeframe: The earliest date to start looking for meeting slots
       - For "today": use current date
       - For "tomorrow": use next day
       - For day names (Monday, Tuesday, etc.): find the NEXT occurrence of that day
       - For "this week": use current date
       - For "next week": use date of next Monday
       - For specific dates: parse and use as-is
       - Format: YYYY-MM-DDTHH:MM:SS+HH:MM
    
    2. end_timeframe: The latest date to stop looking for meeting slots
       - If specific day mentioned: use same day as start_timeframe
       - If "this week" mentioned: use end of current week (Friday)
       - If "next week" mentioned: use end of next week (Friday)  
       - If range mentioned (e.g., "Monday to Wednesday"): use end of range
       - Format: YYYY-MM-DDTHH:MM:SS+HH:MM
    
    3. duration_minutes: Meeting duration in minutes
       - Parse explicit durations: "30 minutes", "1 hour", "2 hours"
       - Convert hours to minutes: 1 hour = 60 minutes
       - Common defaults: "quick chat" = 15 min, "brief meeting" = 30 min
       - If no duration specified: default to 60 minutes
    ### ✅ Few-shot Examples (Context: Saturday, 19th July 2025)
    
    #### 🗓️ Example 1
    
    **Input:** `"Let's meet Thursday"`
        
      "StartTime": "2025-07-24T00:00:00+05:30",
      "EndTime": "2025-07-24T23:59:59+05:30",
      "DurationMinutes": 60
        
    #### 🗓️ Example 2
    
    **Input:** `"30 minute call this week"`
        
      "StartTime": "2025-07-19T00:00:00+05:30",
      "EndTime": "2025-07-25T23:59:59+05:30",
      "DurationMinutes": 30
        
    #### 🗓️ Example 3
    
    **Input:** `"2 hour session tomorrow"`
    
      "StartTime": "2025-07-20T00:00:00+05:30",
      "EndTime": "2025-07-20T23:59:59+05:30",
      "DurationMinutes": 120
    
    #### 🗓️ Example 4
    
    **Input:** `"Meeting Monday to Wednesday"`
    
      "StartTime": "2025-07-21T00:00:00+05:30",
      "EndTime": "2025-07-23T23:59:00+05:30",
      "DurationMinutes": 60
    
    Be precise with date calculations and always consider the current date context.

    #### 🗓️ Example 5
    
    **Input:** `"Let's meet Thursday 11:00 AM for an hour"`
        
      "StartTime": "2025-07-24T11:00:00+05:30",
      "EndTime": "2025-07-24T12:00:00+05:30",
      "DurationMinutes": 60
    
    #### 🗓️ Example 6

    **Input:** `"Let's meet Wednesday 10:00 AM"`
        
      "StartTime": "2025-07-23T10:00:00+05:30",
      "EndTime": "2025-07-23T23:59:59+05:30",
      "DurationMinutes": 60

    
    """,
)

