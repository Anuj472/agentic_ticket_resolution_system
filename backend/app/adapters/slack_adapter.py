from typing import Dict, Any
from app.adapters.base import BaseAdapter
from app.schemas.ticket import UniversalTicket


class SlackAdapter(BaseAdapter):
    """
    Adapter for Slack Events API (e.g., app_mention or message events).
    Expects a payload like:
    {
        "event": {
            "type": "message",
            "text": "My printer is broken",
            "user": "U12345",
            "ts": "1234567890.123456",
            "channel": "C12345"
        }
    }
    """

    def normalize(self, payload: Dict[str, Any]) -> UniversalTicket:
        event = payload.get("event", {})
        if not event:
            raise ValueError("Invalid Slack payload: missing 'event' key")

        text = event.get("text", "")
        # A simple heuristic: first line is title, rest is description
        lines = text.split("\n", 1)
        title = lines[0].strip() if lines else "Slack Request"
        description = lines[1].strip() if len(lines) > 1 else title

        # In a real app, you would resolve the Slack user ID (U12345) to an email address
        # via the Slack API (users.info). For now, we mock the email.
        slack_user_id = event.get("user", "unknown_user")
        submitter_email = f"{slack_user_id}@slack.local"

        return UniversalTicket(
            title=title or "Empty Slack Message",
            description=description or "No description provided",
            source="slack",
            source_ref_id=event.get("ts", ""),
            submitter_email=submitter_email,
            metadata=payload,
        )
