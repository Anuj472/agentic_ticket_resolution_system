from typing import Dict, Any
from app.adapters.base import BaseAdapter
from app.schemas.ticket import UniversalTicket
import re

class EmailAdapter(BaseAdapter):
    """
    Adapter for parsed Email payloads (e.g., from IMAP poller or SendGrid Inbound Parse).
    Expects a payload like:
    {
        "subject": "System is down",
        "body": "The main server is not responding since 9 AM.",
        "from": "user@example.com",
        "message_id": "<1234567890@mail.example.com>",
        "priority_header": "High"
    }
    """
    
    def normalize(self, payload: Dict[str, Any]) -> UniversalTicket:
        subject = payload.get("subject", "No Subject")
        body = payload.get("body", "No body content")
        sender = payload.get("from", "")
        message_id = payload.get("message_id", "")
        
        # Extract raw email address if in format "Name <email@domain.com>"
        email_match = re.search(r'<([^>]+)>', sender)
        submitter_email = email_match.group(1) if email_match else sender
        
        return UniversalTicket(
            title=subject.strip(),
            description=body.strip(),
            source="email",
            source_ref_id=message_id,
            submitter_email=submitter_email.strip(),
            priority_hint=payload.get("priority_header"),
            metadata=payload
        )
