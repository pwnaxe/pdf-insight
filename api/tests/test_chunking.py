from app.chunking import chunk_pages
from app.pdf import PageText


def pages(*sizes: int) -> list[PageText]:
    return [PageText(i, "x" * size) for i, size in enumerate(sizes, start=1)]


def test_single_chunk() -> None:
    plan = chunk_pages(pages(100, 200), chunk_chars=1000, max_chunks=5)
    assert len(plan.chunks) == 1
    assert [p.number for p in plan.chunks[0]] == [1, 2]
    assert not plan.truncated


def test_whole_pages_per_chunk() -> None:
    plan = chunk_pages(pages(600, 600, 600), chunk_chars=1000, max_chunks=5)
    assert [[p.number for p in c] for c in plan.chunks] == [[1], [2], [3]]


def test_packs_pages_greedily() -> None:
    plan = chunk_pages(pages(400, 400, 400, 400), chunk_chars=1000, max_chunks=5)
    assert [[p.number for p in c] for c in plan.chunks] == [[1, 2], [3, 4]]


def test_huge_page_split_by_paragraphs() -> None:
    text = "\n".join(["a" * 40] * 10)
    plan = chunk_pages([PageText(7, text)], chunk_chars=100, max_chunks=10)
    assert len(plan.chunks) > 1
    for chunk in plan.chunks:
        assert sum(len(p.text) for p in chunk) <= 100
        assert all(p.number == 7 for p in chunk)
    joined = "\n".join(p.text for c in plan.chunks for p in c)
    assert joined.replace("\n", "") == text.replace("\n", "")


def test_huge_single_line_is_hard_cut() -> None:
    plan = chunk_pages([PageText(1, "y" * 250)], chunk_chars=100, max_chunks=10)
    assert [sum(len(p.text) for p in c) for c in plan.chunks] == [100, 100, 50]


def test_max_chunks_truncates() -> None:
    plan = chunk_pages(pages(900, 900, 900, 900), chunk_chars=1000, max_chunks=2)
    assert len(plan.chunks) == 2
    assert plan.truncated


def test_empty() -> None:
    plan = chunk_pages([], chunk_chars=1000, max_chunks=2)
    assert plan.chunks == []
    assert not plan.truncated
