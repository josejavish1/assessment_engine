import asyncio
from typing import AsyncGenerator

class SseHeartbeatReaper:
    def __init__(self, heartbeat_interval_seconds: float = 15.0):
        self.interval = heartbeat_interval_seconds

    async def wrap_with_heartbeat(self, event_stream: AsyncGenerator[str, None]) -> AsyncGenerator[str, None]:
        """Wrap an SSE stream to inject periodic heartbeats. If the client disconnects, a socket exception terminates the generator and cleans up memory."""
        next_task = None
        try:
            while True:
                if next_task is None:
                    next_task = asyncio.create_task(event_stream.__anext__())
                done, _ = await asyncio.wait([next_task], timeout=self.interval)
                if done:
                    try:
                        event = next_task.result()
                        next_task = None
                        yield event
                    except StopAsyncIteration:
                        break
                else:
                    # Inject a standard W3C SSE comment to verify that the socket is still alive.
                    yield ": ping\n\n"
        except (StopAsyncIteration, GeneratorExit, BrokenPipeError, ConnectionResetError, asyncio.CancelledError):
            pass
        finally:
            if next_task and not next_task.done():
                next_task.cancel()
                try:
                    await next_task
                except (RuntimeError, ValueError, KeyError, OSError, TypeError, asyncio.CancelledError):
                    pass
