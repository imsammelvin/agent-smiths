from datetime import datetime, timedelta
import ast
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from src.agents.priority_agent import get_priority_async
import re

def find_earliest_meeting_slot(slots_input, meeting_duration_minutes, metadata):
    """
    Find the earliest available meeting slot given available slots and meeting duration.
    
    Args:
        slots_input (str): String containing available slots in format:
                          "slot 1 : 2025-07-23T10:30:00+05:30 - 2025-07-23T11:59:00+05:30\n slot 2 : ..."
        meeting_duration_minutes (int): Duration of meeting in minutes
    
    Returns:
        dict: Contains earliest_start, end_time, and duration
    """
    
    # Parse slots from input string
    slot_pattern = r'slot \d+ : (\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\+\d{2}:\d{2}) - (\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\+\d{2}:\d{2})'
    matches = re.findall(slot_pattern, slots_input)
    print("mm",matches)
    
    if not matches:
        return {"error": "No valid slots found"}
    
    # Convert to datetime objects and find earliest slot that fits the meeting
    meeting_duration = timedelta(minutes=meeting_duration_minutes)
    earliest_slot = None
    
    for start_str, end_str in matches:
        start_time = datetime.fromisoformat(start_str)
        end_time = datetime.fromisoformat(end_str)
        slot_duration = end_time - start_time
        
        # Check if this slot can accommodate the meeting duration
        if slot_duration >= meeting_duration - timedelta(minutes=1):
            if earliest_slot is None or start_time < earliest_slot['start']:
                earliest_slot = {
                    'start': start_time,
                    'end': end_time,
                    'slot_duration': slot_duration
                }
    
    if earliest_slot is None:
        return {"error": "No slot can accommodate the meeting duration"}
    
    # Calculate meeting end time
    meeting_start = earliest_slot['start']
    meeting_end = meeting_start + meeting_duration
    
    return {
        "start_time_of_meeting": str(meeting_start.isoformat()),
        "end_time_of_meeting": str(meeting_end.isoformat()),
        "duration_minutes": f"{meeting_duration_minutes}",
        "metadata": metadata
    }


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

# def retrieve_calendar_events(user, start, end):
#     events_list = []
#     token_path = "Keys/"+user.split("@")[0]+".token"
#     user_creds = Credentials.from_authorized_user_file(token_path)
#     calendar_service = build("calendar", "v3", credentials=user_creds)
#     events_result = calendar_service.events().list(
#         calendarId='primary', 
#         timeMin=start,
#         timeMax=end,
#         singleEvents=True,
#         orderBy='startTime'
#     ).execute()
#     events = events_result.get('items', [])
    
#     for event in events: 
#         attendee_list = []
#         try:
#             for attendee in event["attendees"]: 
#                 attendee_list.append(attendee['email'])
#         except: 
#             attendee_list.append("SELF")
        
#         start_time = event["start"]["dateTime"]
#         end_time = event["end"]["dateTime"]
#         events_list.append({
#             "StartTime": start_time, 
#             "EndTime": end_time, 
#             "NumAttendees": len(set(attendee_list)), 
#             "Attendees": list(set(attendee_list)),
#             "Summary": event["summary"]
#         })

#     print(events_list)
#     return events_list

import time
import asyncio
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

import asyncio
import nest_asyncio
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

# Enable nested event loops (useful in Jupyter notebooks)
nest_asyncio.apply()


def retrieve_calendar_events(user, start, end):
    events_list = []
    token_path = "Keys/"+user.split("@")[0]+".token"
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
    
    for event in events: 
        attendee_list = []
        try:
            for attendee in event["attendees"]: 
                attendee_list.append(attendee['email'])
        except: 
            attendee_list.append("SELF")
        
        start_time = event["start"]["dateTime"]
        end_time = event["end"]["dateTime"]
        
        # Create event data structure
        event_data = {
            "StartTime": start_time, 
            "EndTime": end_time, 
            "NumAttendees": len(set(attendee_list)), 
            "Attendees": list(set(attendee_list)),
            "Summary": event["summary"]
        }
        
        events_list.append(event_data)
    
    print(events_list)
    return events_list

def retrieve_calendar_events_priority(user, start, end, event_priority, num_attend):
    events_list = []
    token_path = "Keys/"+user.split("@")[0]+".token"
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
    
    # Define priority hierarchy for comparison
    priority_levels = {"low": 1, "mid": 2, "high": 3}
    min_priority_level = priority_levels.get(event_priority.lower(), 2)  # Default to "mid" if invalid
    
    for event in events: 
        attendee_list = []
        try:
            for attendee in event["attendees"]: 
                attendee_list.append(attendee['email'])
        except: 
            attendee_list.append("SELF")
        
        start_time = event["start"]["dateTime"]
        end_time = event["end"]["dateTime"]
        
        # Create event data structure
        event_data = {
            "StartTime": start_time, 
            "EndTime": end_time, 
            "NumAttendees": len(set(attendee_list)), 
            "Attendees": list(set(attendee_list)),
            "Summary": event["summary"]
        }
        
        # Get priority for this meeting
        try:
            # Convert event data to string format for the agent
            event_string = str(event_data)
            # Now asyncio.run() will work even in nested event loops
            priority_result = asyncio.run(get_priority_async(event_string))
            priority = priority_result.data.priority
        except Exception as e:
            print(f"Error getting priority for event '{event['summary']}': {e}")
            priority = "mid"  # Default priority if agent fails
        
        # Add priority to the event data
        event_data["Priority"] = priority
        
        # Only append if event priority is >= minimum threshold
        event_priority_level = priority_levels.get(priority.lower(), 2)  # Default to "mid"
        if event_priority_level > min_priority_level:
            events_list.append(event_data)
        elif event_priority_level == min_priority_level:
            if int(event_data["NumAttendees"]) > num_attend:
                events_list.append(event_data)
            elif int(event_data["NumAttendees"]) == num_attend:
                pass
    
    print(events_list)
    return events_list

# Usage remains the same:
# events = retrieve_calendar_events(user, start_date, end_date)

# Usage remains the same:
# events = retrieve_calendar_events(user, start_date, end_date)

# Usage example:
# async def main():
#     start_time = time.time()
#     events_with_priorities = await retrieve_calendar_events(
#         user="user@example.com", 
#         start="2025-07-22T00:00:00+05:30", 
#         end="2025-07-22T23:59:59+05:30",
#         meeting_priority_agent=meeting_priority_agent
#     )
#     end_time = time.time()
#     print(f"Processing time: {end_time - start_time} seconds")

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

def get_free_time_slots(attendees, duration_minutes, start_date, end_date,slots_agent):
    user_availabilities = []
    users_schedule_dict = {}
    duration_minutes = int(duration_minutes)
    
    # Parse input dates
    start_dt = datetime.fromisoformat(start_date)
    end_dt = datetime.fromisoformat(end_date)
    
    # Input validation
    if start_dt >= end_dt:
        return "Error: Start date must be before end date", {}
    
    if duration_minutes <= 0:
        return "Error: Duration must be positive", {}
    
    attendees = parse_list(attendees)
    if not attendees:
        return "Error: No attendees provided", {}
    
    # Collect all busy periods and build users_schedule_dict
    for user in attendees:
        users_schedule_dict[user] = []
        try:
            events = retrieve_calendar_events(user, start_date, end_date)
            for event in events:
                event_start = datetime.fromisoformat(event["StartTime"])
                event_end = datetime.fromisoformat(event["EndTime"])
                
                # Store original event info in users_schedule_dict
                users_schedule_dict[user].append(event)
                
                # Clip events to the search window for availability calculation
                clipped_start = max(event_start, start_dt)
                clipped_end = min(event_end, end_dt)
                
                # Only add if there's actual overlap with our time window
                if clipped_start < clipped_end:
                    user_availabilities.append((clipped_start, clipped_end))
        except Exception as e:
            print(f"Warning: Could not retrieve events for {user}: {e}")
            continue
    
    # Handle case where no events found
    if not user_availabilities:
        return f"slot 1 : {start_date} - {end_date}\n ", users_schedule_dict
    
    merged_unavailable = merge_intervals(user_availabilities)
    available = []
    duration = timedelta(minutes=duration_minutes)
    
    # Check slot before first busy period
    if len(merged_unavailable) > 0:
        gap_before = merged_unavailable[0][0] - start_dt
        if gap_before >= duration:
            available.append((start_dt, merged_unavailable[0][0]))
    
    # Check gaps between busy periods
    for i in range(1, len(merged_unavailable)):
        gap_duration = merged_unavailable[i][0] - merged_unavailable[i-1][1]
        if gap_duration >= duration:
            available.append((merged_unavailable[i-1][1], merged_unavailable[i][0]))
    
    # Check slot after last busy period
    if len(merged_unavailable) > 0:
        gap_after = end_dt - merged_unavailable[-1][1]
        if gap_after >= duration:
            available.append((merged_unavailable[-1][1], end_dt))
    
    # Format output consistently (using isoformat to match your end_date parameter)
    if not available:
        return "No available time slots found for the specified duration\n ", users_schedule_dict
    
    slots = ""
    idx = 1
    for slot_start, slot_end in available:
        # Use consistent isoformat for both start and end
        start_str = slot_start.isoformat()
        end_str = slot_end.isoformat()
        slots += f"slot {idx} : {start_str} - {end_str}\n "
        idx += 1
    
    return slots, users_schedule_dict

def get_free_time_slots_priority(attendees, duration_minutes, start_date, end_date, event_priority, num_attend):
    user_availabilities = []
    duration_minutes = int(duration_minutes)
    
    # Parse input dates
    start_dt = datetime.fromisoformat(start_date)
    end_dt = datetime.fromisoformat(end_date)
    
    # Input validation
    if start_dt >= end_dt:
        return "Error: Start date must be before end date"
    
    if duration_minutes <= 0:
        return "Error: Duration must be positive"
    
    attendees = parse_list(attendees)
    if not attendees:
        return "Error: No attendees provided"
    
    # Collect all busy periods
    for user in attendees:
        try:
            events = retrieve_calendar_events_priority(user, start_date, end_date, event_priority, num_attend)
            for event in events:
                event_start = datetime.fromisoformat(event["StartTime"])
                event_end = datetime.fromisoformat(event["EndTime"])
                
                # Clip events to the search window
                clipped_start = max(event_start, start_dt)
                clipped_end = min(event_end, end_dt)
                
                # Only add if there's actual overlap with our time window
                if clipped_start < clipped_end:
                    user_availabilities.append((clipped_start, clipped_end))
        except Exception as e:
            print(f"Warning: Could not retrieve events for {user}: {e}")
            continue
    
    # Handle case where no events found
    if not user_availabilities:
        return f"slot 1 : {start_date} - {end_date}\n "
    
    merged_unavailable = merge_intervals(user_availabilities)
    available = []
    duration = timedelta(minutes=duration_minutes)
    
    # Check slot before first busy period
    if len(merged_unavailable) > 0:
        gap_before = merged_unavailable[0][0] - start_dt
        if gap_before >= duration:
            available.append((start_dt, merged_unavailable[0][0]))
    
    # Check gaps between busy periods
    for i in range(1, len(merged_unavailable)):
        gap_duration = merged_unavailable[i][0] - merged_unavailable[i-1][1]
        if gap_duration >= duration:
            available.append((merged_unavailable[i-1][1], merged_unavailable[i][0]))
    
    # Check slot after last busy period
    if len(merged_unavailable) > 0:
        gap_after = end_dt - merged_unavailable[-1][1]
        if gap_after >= duration:
            available.append((merged_unavailable[-1][1], end_dt))
    
    # Format output consistently (using isoformat to match your end_date parameter)
    if not available:
        return "No available time slots found for the specified duration\n "
    
    slots = ""
    idx = 1
    for slot_start, slot_end in available:
        # Use consistent isoformat for both start and end
        start_str = slot_start.isoformat()
        end_str = slot_end.isoformat()
        slots += f"slot {idx} : {start_str} - {end_str}\n "
        idx += 1
    
    return slots