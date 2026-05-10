from abc import ABC, abstractmethod
from typing import Dict, Any
from app.schemas.ticket import UniversalTicket

class BaseAdapter(ABC):
    """Abstract base class for all omnichannel source adapters."""

    @abstractmethod
    def normalize(self, payload: Dict[str, Any]) -> UniversalTicket:
        """
        Parses a source-specific payload and converts it into a UniversalTicket.
        Raises ValueError if the payload is invalid or cannot be parsed.
        """
        pass
