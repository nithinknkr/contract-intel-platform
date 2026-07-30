import uuid

from pydantic import BaseModel


class AskRequest(BaseModel):
    question: str


class CitationOut(BaseModel):
    chunk_id: str
    quote: str


class AskResponse(BaseModel):
    answer: str
    citations: list[CitationOut]
    retrieved_chunk_ids: list[uuid.UUID]