def get_attendees_with_from(data):
    """
    Extract attendees emails as a list along with From email.
    If Attendees is just ['SELF'], return only the From email.
    
    Args:
        data (dict): The input data containing From and Attendees
        
    Returns:
        list: List of email addresses
    """
    from_email = data.get("From", "")
    attendees = data.get("Attendees", [])
    
    # Extract emails from attendees list
    attendee_emails = []
    for attendee in attendees:
        if isinstance(attendee, dict) and "email" in attendee:
            attendee_emails.append(attendee["email"])
        elif isinstance(attendee, str):
            attendee_emails.append(attendee)
    
    # Special case: if attendees is just ['SELF'], return only From email
    if attendee_emails == ['SELF']:
        return [from_email]
    
    # Otherwise, combine From email with attendees emails
    all_emails = [from_email] + attendee_emails
    
    # Remove duplicates while preserving order
    seen = set()
    result = []
    for email in all_emails:
        if email and email not in seen:
            seen.add(email)
            result.append(email)
    
    return result