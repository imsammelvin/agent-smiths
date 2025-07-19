from mcp.server.fastmcp import FastMCP
from mcp.server import Server
import json
import logging
from datetime import datetime, timezone, timedelta
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from mcp.server.sse import SseServerTransport
import argparse
from starlette.routing import Mount, Route
from starlette.applications import Starlette
from starlette.requests import Request
import uvicorn

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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


@mcp.tool()
def get_current_date() -> str:
    """Return the current date/time as an ISO-formatted string."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


    

@mcp.tool()
def retrieve_calendar_events(user: str, start: str, end: str):
    """
    Retrieve calendar events for a user within a specified time range.
    
    Args:
        user: Email address of the user
        start: Start time in ISO format (e.g., '2024-01-01T00:00:00Z')
        end: End time in ISO format (e.g., '2024-01-31T23:59:59Z')
    
    Returns:
        List of calendar events with details
    """
    logger.info(f"Retrieving calendar events for {user} from {start} to {end}")
    events_list = []
    
    try:
        token_path = "Keys/" + user.split("@")[0] + ".token"
        user_creds = Credentials.from_authorized_user_file(token_path)
        calendar_service = build("calendar", "v3", credentials=user_creds)
        
        events_result = calendar_service.events().list(
            calendarId='primary', 
            timeMin=start,
            timeMax=end,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        events = events_result.get('items', [])
        logger.info(f"Found {len(events)} events")
        
        for event in events: 
            attendee_list = []
            try:
                for attendee in event.get("attendees", []): 
                    attendee_list.append(attendee['email'])
            except: 
                attendee_list.append("SELF")
            
            start_time = event["start"].get("dateTime", event["start"].get("date"))
            end_time = event["end"].get("dateTime", event["end"].get("date"))
            
            events_list.append({
                "StartTime": start_time, 
                "EndTime": end_time, 
                "NumAttendees": len(set(attendee_list)), 
                "Attendees": list(set(attendee_list)),
                "Summary": event.get("summary", "No title")
            })
        
        return events_list
        
    except Exception as e:
        logger.error(f"Error retrieving calendar events: {e}")
        raise

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


    