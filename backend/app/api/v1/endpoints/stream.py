import asyncio
import json
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from app.core.dependencies import get_current_user
from app.models.user import User

router = APIRouter()
_subscribers: dict[str, list] = {}


async def _event_generator(user_id: str):
    queue = asyncio.Queue()
    _subscribers.setdefault(user_id, []).append(queue)
    try:
        yield 'data: {"type":"connected"}\n\n'
        while True:
            try:
                message = await asyncio.wait_for(queue.get(), timeout=30.0)
                yield f"data: {json.dumps(message)}\n\n"
            except asyncio.TimeoutError:
                yield 'data: {"type":"ping"}\n\n'
    finally:
        _subscribers[user_id].remove(queue)


async def push_event(user_id: str, event: dict):
    for queue in _subscribers.get(user_id, []):
        await queue.put(event)


async def broadcast_event(event: dict):
    for queues in _subscribers.values():
        for queue in queues:
            await queue.put(event)


@router.get("/stream")
async def ticket_stream(current_user: User = Depends(get_current_user)):
    return StreamingResponse(
        _event_generator(str(current_user.id)),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Access-Control-Allow-Origin": "*",
        },
    )
