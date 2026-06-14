from app.adapters.base import BaseAdapter
from app.adapters.slack_adapter import SlackAdapter
from app.adapters.email_adapter import EmailAdapter


def get_adapter(source: str) -> BaseAdapter:
    """
    Factory function to get the appropriate adapter based on the source name.
    Raises ValueError if the adapter is not found.
    """
    adapters = {
        "slack": SlackAdapter(),
        "email": EmailAdapter(),
    }

    adapter = adapters.get(source.lower())
    if not adapter:
        raise ValueError(f"Unknown source adapter: {source}")

    return adapter
