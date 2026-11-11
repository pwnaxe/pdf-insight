from dataclasses import dataclass

from app.pdf import PageText


@dataclass(frozen=True)
class ChunkPlan:
    chunks: list[list[PageText]]
    truncated: bool


def _split_page(page: PageText, limit: int) -> list[PageText]:
    if len(page.text) <= limit:
        return [page]
    pieces: list[PageText] = []
    current = ""
    for paragraph in page.text.split("\n"):
        while len(paragraph) > limit:
            if current:
                pieces.append(PageText(page.number, current))
                current = ""
            pieces.append(PageText(page.number, paragraph[:limit]))
            paragraph = paragraph[limit:]
        joined = f"{current}\n{paragraph}" if current else paragraph
        if len(joined) > limit:
            pieces.append(PageText(page.number, current))
            current = paragraph
        else:
            current = joined
    if current:
        pieces.append(PageText(page.number, current))
    return pieces


def chunk_pages(pages: list[PageText], chunk_chars: int, max_chunks: int) -> ChunkPlan:
    chunks: list[list[PageText]] = []
    current: list[PageText] = []
    size = 0
    for page in pages:
        for piece in _split_page(page, chunk_chars):
            if current and size + len(piece.text) > chunk_chars:
                chunks.append(current)
                current, size = [], 0
            current.append(piece)
            size += len(piece.text)
    if current:
        chunks.append(current)

    truncated = len(chunks) > max_chunks
    return ChunkPlan(chunks[:max_chunks], truncated)
