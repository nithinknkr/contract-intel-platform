import re
import hashlib
from dataclasses import dataclass


@dataclass
class ChunkResult:
    content: str
    char_start: int
    char_end: int
    chunk_index: int


CHUNK_SIZE = 1000
CHUNK_OVERLAP = 150


def _content_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def chunk_text(full_text: str) -> list[ChunkResult]:
    """
    Splits full_text into overlapping chunks of ~CHUNK_SIZE chars,
    preferring to break on paragraph boundaries, falling back to
    sentence boundaries, falling back to a hard char cut.
    Offsets are tracked against the ORIGINAL full_text, not per-chunk.
    """
    if not full_text.strip():
        return []

    chunks: list[ChunkResult] = []
    text_len = len(full_text)
    pos = 0
    index = 0

    while pos < text_len:
        target_end = min(pos + CHUNK_SIZE, text_len)

        if target_end < text_len:
            end = _find_break_point(full_text, pos, target_end)
        else:
            end = target_end

        chunk_str = full_text[pos:end]

        chunks.append(
            ChunkResult(
                content=chunk_str,
                char_start=pos,
                char_end=end,
                chunk_index=index,
            )
        )
        index += 1

        if end >= text_len:
            break

        # Next chunk starts CHUNK_OVERLAP chars before this one ended
        pos = max(end - CHUNK_OVERLAP, pos + 1)  # +1 guards against infinite loop

    return chunks


def _find_break_point(text: str, start: int, target_end: int) -> int:
    """
    Looks backward from target_end for a paragraph break (\n\n), then a
    sentence break (. ! ?), then just gives up and hard-cuts at target_end.
    Never searches before `start` — a chunk can't be shorter than nothing.
    """
    search_window = text[start:target_end]

    para_break = search_window.rfind("\n\n")
    if para_break != -1 and para_break > len(search_window) * 0.5:
        return start + para_break + 2  # skip past the \n\n itself

    sentence_break = max(
        search_window.rfind(". "),
        search_window.rfind("! "),
        search_window.rfind("? "),
    )
    if sentence_break != -1 and sentence_break > len(search_window) * 0.5:
        return start + sentence_break + 2

    return target_end