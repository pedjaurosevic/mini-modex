"""OpenAI-compatible API server for Kon.

Exposes /v1/chat/completions and /v1/models endpoints.
Designed to be a drop-in replacement for the PolyStrata API.
"""

from __future__ import annotations

import asyncio
import json
import uuid
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field

from kon import config
from kon.runtime import ConversationRuntime
from kon.tools import DEFAULT_TOOLS, get_tools


# =================================================================================================
# Request/Response Models (OpenAI-compatible)
# =================================================================================================


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatCompletionRequest(BaseModel):
    model: str
    messages: list[ChatMessage]
    max_tokens: int | None = None
    stream: bool = False
    temperature: float | None = None
    top_p: float | None = None


class ChatCompletionResponse(BaseModel):
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: list[dict]
    usage: dict


class StreamChunk(BaseModel):
    id: str
    object: str = "chat.completion.chunk"
    created: int
    model: str
    choices: list[dict]


class ModelInfo(BaseModel):
    id: str
    object: str = "model"
    created: int = 0
    owned_by: str = "kon"


# =================================================================================================
# Server
# =================================================================================================


class KonApiServer:
    """OpenAI-compatible API server backed by Kon."""

    def __init__(
        self,
        host: str = "0.0.0.0",
        port: int = 18083,
        model: str | None = None,
        provider: str | None = None,
        api_key: str | None = None,
        base_url: str | None = None,
    ) -> None:
        self.host = host
        self.port = port
        self.model = model or config.llm.default_model
        self.provider = provider
        self.api_key = api_key
        self.base_url = base_url
        self.runtime: ConversationRuntime | None = None
        self.app = FastAPI(title="Kon API", version="0.4.3")
        self._setup_routes()

    def _setup_routes(self) -> None:
        @self.app.get("/v1/models")
        async def list_models():
            return {
                "object": "list",
                "data": [
                    ModelInfo(
                        id=self.model,
                        created=int(datetime.now().timestamp()),
                    ).model_dump()
                ],
            }

        @self.app.get("/v1/models/{model_id}")
        async def retrieve_model(model_id: str):
            return ModelInfo(
                id=model_id,
                created=int(datetime.now().timestamp()),
            ).model_dump()

        @self.app.post("/v1/chat/completions")
        async def create_completion(request: ChatCompletionRequest):
            if request.stream:
                return StreamingResponse(
                    self._stream_completion(request),
                    media_type="text/event-stream",
                )
            return await self._complete(request)

    async def _initialize_runtime(self) -> ConversationRuntime:
        """Lazy-initialize the runtime."""
        if self.runtime is None:
            tools = get_tools(DEFAULT_TOOLS)
            self.runtime = ConversationRuntime(
                cwd=str(Path.cwd()),
                model=self.model,
                model_provider=self.provider,
                api_key=self.api_key,
                base_url=self.base_url,
                thinking_level=config.llm.default_thinking_level,
                tools=tools,
            )
            self.runtime.initialize()
        return self.runtime

    async def _complete(self, request: ChatCompletionRequest) -> JSONResponse:
        """Non-streaming completion."""
        runtime = await self._initialize_runtime()
        if runtime.agent is None:
            return JSONResponse(
                status_code=503,
                content={"error": "Agent not initialized"},
            )

        # Build messages from request
        messages = [
            {"role": m.role, "content": m.content} for m in request.messages
        ]

        # Get the last user message
        user_messages = [m for m in messages if m["role"] == "user"]
        if not user_messages:
            return JSONResponse(
                status_code=400,
                content={"error": "No user messages"},
            )

        query = user_messages[-1]["content"]

        # Run the agent
        try:
            events = runtime.agent.run(query)
            stop_reason = None
            final_text = ""
            async for event in events:
                from kon.events import AgentEndEvent, TurnEndEvent
                from kon.core.types import TextContent
                if isinstance(event, TurnEndEvent) and event.assistant_message:
                    text = "".join(
                        p.text for p in event.assistant_message.content
                        if isinstance(p, TextContent)
                    ).strip()
                    if text:
                        final_text = text
                elif isinstance(event, AgentEndEvent):
                    stop_reason = event.stop_reason

            # Build response
            response = ChatCompletionResponse(
                id=f"chatcmpl-{uuid.uuid4().hex[:12]}",
                created=int(datetime.now().timestamp()),
                model=request.model,
                choices=[
                    {
                        "index": 0,
                        "message": {
                            "role": "assistant",
                            "content": final_text,
                        },
                        "finish_reason": "stop" if stop_reason else "error",
                    }
                ],
                usage={
                    "prompt_tokens": 0,
                    "completion_tokens": len(final_text.split()),
                    "total_tokens": len(final_text.split()),
                },
            )
            return JSONResponse(response.model_dump())

        except Exception as e:
            return JSONResponse(
                status_code=500,
                content={"error": str(e)},
            )

    async def _stream_completion(self, request: ChatCompletionRequest):
        """Streaming completion."""
        runtime = await self._initialize_runtime()
        if runtime.agent is None:
            yield f"data: {json.dumps({'error': 'Agent not initialized'})}\n\n"
            yield "data: [DONE]\n\n"
            return

        user_messages = [m for m in request.messages if m["role"] == "user"]
        if not user_messages:
            yield f"data: {json.dumps({'error': 'No user messages'})}\n\n"
            yield "data: [DONE]\n\n"
            return

        query = user_messages[-1]["content"]

        try:
            events = runtime.agent.run(query)
            full_text = ""
            async for event in events:
                from kon.events import TurnEndEvent
                from kon.core.types import TextContent
                if isinstance(event, TurnEndEvent) and event.assistant_message:
                    text = "".join(
                        p.text for p in event.assistant_message.content
                        if isinstance(p, TextContent)
                    ).strip()
                    if text != full_text:
                        new_text = text[len(full_text):]
                        if new_text:
                            full_text = text
                            chunk = StreamChunk(
                                id=f"chatcmpl-{uuid.uuid4().hex[:12]}",
                                created=int(datetime.now().timestamp()),
                                model=request.model,
                                choices=[
                                    {
                                        "index": 0,
                                        "delta": {"role": "assistant", "content": new_text},
                                        "finish_reason": None,
                                    }
                                ],
                            )
                            yield f"data: {json.dumps(chunk.model_dump())}\n\n"

            # Final chunk
            final_chunk = StreamChunk(
                id=f"chatcmpl-{uuid.uuid4().hex[:12]}",
                created=int(datetime.now().timestamp()),
                model=request.model,
                choices=[
                    {
                        "index": 0,
                        "delta": {},
                        "finish_reason": "stop",
                    }
                ],
            )
            yield f"data: {json.dumps(final_chunk.model_dump())}\n\n"
            yield "data: [DONE]\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
            yield "data: [DONE]\n\n"

def main() -> None:
    """Run the API server."""
    server = KonApiServer(
        host="0.0.0.0",
        port=18083,
        model=config.llm.default_model,
        provider=config.llm.default_provider,
    )
    print(f"Kon API server starting on http://0.0.0.0:18083")
    print(f"Model: {server.model}")
    print(f"Provider: {server.provider}")
    # uvicorn.run() manages its own event loop
    import uvicorn
    uvicorn.run(server.app, host=server.host, port=server.port, log_level="info")


if __name__ == "__main__":
    main()
