from mcp.server.fastmcp import FastMCP
from mcp.server import Server
import json
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timezone, timedelta
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from mcp.server.sse import SseServerTransport
import argparse
from starlette.routing import Mount, Route
from pydantic import BaseModel
from starlette.applications import Starlette
from starlette.requests import Request
import uvicorn
import os
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai import Agent
import ast


# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_URL = f"http://localhost:8000/v1"

os.environ["BASE_URL"]    = BASE_URL
os.environ["OPENAI_API_KEY"] = "abc-123"  

provider = OpenAIProvider(
    base_url=os.environ["BASE_URL"],
    api_key=os.environ["OPENAI_API_KEY"],
)
model = OpenAIModel("Qwen3-8B", provider=provider)

# Define response model for meeting extraction
def retrieve_calendar_events(user, start, end):
    events_list = []
    token_path = "Keys/"+user.split("@")[0]+".token"
    user_creds = Credentials.from_authorized_user_file(token_path)
    calendar_service = build("calendar", "v3", credentials=user_creds)
    events_result = calendar_service.events().list(calendarId='primary', timeMin=start,timeMax=end,singleEvents=True,orderBy='startTime').execute()
    events = events_result.get('items')
    
    for event in events : 
        attendee_list = []
        try:
            for attendee in event["attendees"]: 
                attendee_list.append(attendee['email'])
        except: 
            attendee_list.append("SELF")
        start_time = event["start"]["dateTime"]
        end_time = event["end"]["dateTime"]
        events_list.append(
            {"StartTime" : start_time, 
             "EndTime": end_time, 
             "NumAttendees" :len(set(attendee_list)), 
             "Attendees" : list(set(attendee_list)),
             "Summary" : event["summary"]})
    return events_list

mcp = FastMCP("scheduler",timeout=120000000)

def create_starlette_app(mcp_server: Server, *, debug: bool = False) -> Starlette:
    """Create a Starlette application that can server the provied mcp server with SSE."""
    sse = SseServerTransport("/messages/")

    async def handle_sse(request: Request) -> None:
        async with sse.connect_sse(
                request.scope,
                request.receive,
                request._send,  # noqa: SLF001
        ) as (read_stream, write_stream):
            await mcp_server.run(
                read_stream,
                write_stream,
                mcp_server.create_initialization_options(),
            )

    return Starlette(
        debug=debug,
        routes=[
            Route("/sse", endpoint=handle_sse),
            Mount("/messages/", app=sse.handle_post_message),
        ],
    )




from datetime import datetime

def merge_intervals(intervals):
    if not intervals:
        return []

    # Sort by start time
    intervals.sort(key=lambda x: x[0])
    merged = [intervals[0]]

    for current_start, current_end in intervals[1:]:
        last_start, last_end = merged[-1]
        if current_start <= last_end:
            merged[-1] = (last_start, max(last_end, current_end))  # Merge overlapping
        else:
            merged.append((current_start, current_end))
    return merged

import ast

def parse_list(maybe_str):
    if isinstance(maybe_str, str):
        return ast.literal_eval(maybe_str)
    return maybe_str  # it's already a list



@mcp.tool()
def get_free_time_slots(attendees, duration_minutes, start_date, end_date):
    """
    Find available time slots for scheduling meetings with multiple attendees.
    
    This function analyzes the calendars of all specified attendees to identify
    time periods when everyone is available for a meeting of the specified duration.
    It retrieves calendar events for each attendee, merges overlapping busy periods,
    and returns the gaps that are long enough to accommodate the requested meeting.
    
    Args:
        attendees (list): List of attendee identifiers (usernames, emails, or IDs)
                         whose calendars will be checked for availability.
        duration_minutes (int): Required meeting duration in minutes. Only time slots
                               with at least this much available time will be returned.
        start_date (str): Start of the search period in ISO format (YYYY-MM-DDTHH:MM:SS)
                         or similar datetime string format.
        end_date (str): End of the search period in ISO format (YYYY-MM-DDTHH:MM:SS)
                       or similar datetime string format.
    
    Returns:
        str: A formatted string containing available time slots, with each slot
             represented as "start_time-end_time,\n " format. Each time is formatted
             as 'YYYY-MM-DD HH:MM:SS timezone_offset'.
    
    Dependencies:
        - retrieve_calendar_events(): Function to fetch calendar events for a user
        - merge_intervals(): Function to merge overlapping time intervals
        - datetime, timedelta: For date/time operations
    
    Example:
        >>> get_free_time_slots(
        ...     attendees=['userone.amd@gmail.com', 'usertwo.amd@gmail.com'],
        ...     duration_minutes=60,
        ...     start_date='2025-07-20T09:00:00',
        ...     end_date='2025-07-20T17:00:00'
        ... )
        '2025-07-20 10:00:00 +05:30-2025-07-20 11:00:00 +05:30,\n 2025-07-20 14:00:00 +05:30-2025-07-20 16:00:00 +05:30,\n '
    
    Note:
        - The function assumes all attendees must be available simultaneously
        - Time slots shorter than duration_minutes are excluded from results
        - Calendar events are expected to have 'StartTime' and 'EndTime' fields
        - Function handles timezone-aware datetime objects
    """

    user_availabilities = []
    duration_minutes = int(duration_minutes)
    
    print(attendees,type(attendees))
    attendees = parse_list(attendees)

    print(attendees,type(attendees))
    print(duration_minutes,type(duration_minutes))
    print(start_date,type(start_date))
    print( datetime.fromisoformat(start_date))
    print(end_date,type(end_date))
    print( datetime.fromisoformat(end_date))
    

    for user in attendees:
        events = retrieve_calendar_events(user, start_date, end_date)
        for event in events:
            start = datetime.fromisoformat(event["StartTime"])
            end = datetime.fromisoformat(event["EndTime"])
            user_availabilities.append((start, end))
    print(user_availabilities)

    merged_unavailable = merge_intervals(user_availabilities)
    available = []
    duration = timedelta(minutes=duration_minutes)
    if merged_unavailable[0][0] -  datetime.fromisoformat(start_date)>=duration:
        available.append((start_date,merged_unavailable[0][0].strftime('%Y-%m-%d %H:%M:%S %z')))
    for i in range(1,len(merged_unavailable)):
        if (merged_unavailable[i][0] - merged_unavailable[i-1][1] )>=duration:
            available.append((merged_unavailable[i-1][1].strftime('%Y-%m-%d %H:%M:%S %z'),merged_unavailable[i][0].strftime('%Y-%m-%d %H:%M:%S %z')))
    if (datetime.fromisoformat(end_date)-merged_unavailable[-1][1])>=duration:
        available.append((merged_unavailable[-1][1].strftime('%Y-%m-%d %H:%M:%S %z'),end_date))
    slots = ""
    for s,e in available:
        slots+= (s+"-"+e+",\n ")
    return slots
    

@mcp.tool()
def get_current_date() -> str:
    """Return the current date/time as an ISO-formatted string."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")




if __name__ == "__main__":
    logger.info("Starting FastMCP server...")
    mcp_server = mcp._mcp_server  # noqa: WPS437
    

    import argparse
    
    parser = argparse.ArgumentParser(description='Run MCP SSE-based server')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to')
    parser.add_argument('--port', type=int, default=8090, help='Port to listen on')
    args = parser.parse_args()

    # Bind SSE request handling to MCP server
    starlette_app = create_starlette_app(mcp_server, debug=True)

    uvicorn.run(
        starlette_app, 
        host=args.host, 
        port=args.port,
        workers=1,  # Use 1 worker with async handling
        loop="asyncio",
        access_log=True,
        log_level="info"
    )


    