# 🧠 AI Scheduling Assistant

An autonomous AI-powered meeting assistant that intelligently handles scheduling, prioritization, and conflict resolution — all without manual back-and-forth.

---

## 📌 Features

- Extracts relevant details from emails and inputs  
- Determines meeting urgency and priority  
- Automatically checks calendars of all attendees  
- Suggests optimal meeting slots  
- Resolves conflicts by evaluating event priorities  

---

## 🔄 Workflow Overview

### 📨 1. Input Processing  
Receives all meeting-related input such as:  
- Email content  
- Attendee details  
- Other metadata  

### 🕒 2. Time Frame Extraction  
Identifies the proposed meeting window from the email body or request.

### 🚦 3. Priority Assessment  
Analyzes the email content to determine the urgency/importance of the meeting.

### 👥 4. User Identification  
Detects involved users based on email or API input.

### 📅 5. Calendar Event Fetching  
Fetches each user's calendar events within the proposed timeframe using the Calendar API.

### ✅ 6. Availability Check  
Checks all attendees’ schedules for overlapping free slots.

### ⚠️ 7. Conflict Resolution (Fallback)  
If no common slot is found:
- Assigns priority scores to all existing calendar events  
- Suggests the least disruptive slot by evaluating overlaps and event importance  

---

## ⚙️ Tech Stack

- **Language**: Python  
- **Calendar API**: Google Calendar  
- **AI Components**: Agentic reasoning system (non-rule-based)  
- **Latency Goal**: Sub-10s response time  

---

## 🎯 Outcome

A fully autonomous meeting scheduler that:
- Understands natural language  
- Respects urgency and user context  
- Minimizes disruption  
- Scales across teams and organizations  
