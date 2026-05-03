from fastapi import Request
from fastapi.responses import JSONResponse


class TicketNotFoundError(Exception):
    pass


class DuplicateTicketError(Exception):
    pass


class EmbeddingError(Exception):
    pass


async def ticket_not_found_handler(request: Request, exc: TicketNotFoundError):
    return JSONResponse(status_code=404, content={"detail": str(exc) or "Ticket not found"})


async def duplicate_ticket_handler(request: Request, exc: DuplicateTicketError):
    return JSONResponse(status_code=409, content={"detail": str(exc) or "Duplicate ticket"})
