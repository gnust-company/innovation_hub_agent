"""Pydantic schemas for the chat API."""
from pydantic import BaseModel, Field


class UserMetadata(BaseModel):
    user_id: str = ""
    username: str = ""
    role: str = ""


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=5000)
    thread_id: str = Field(default="")
    user_metadata: UserMetadata = Field(default_factory=UserMetadata)


class ChatResponse(BaseModel):
    answer: str
    sources: list[str] = Field(default_factory=list)
    thread_id: str


class StreamEvent(BaseModel):
    type: str  # "token" | "tool_call" | "tool_result" | "sources" | "done" | "error"
    content: str = ""
    name: str = ""
    files: list[str] = Field(default_factory=list)


class HealthResponse(BaseModel):
    status: str
    wiki_path: str
    model: str
