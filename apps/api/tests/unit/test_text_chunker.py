import pytest

from app.services.text_chunker import chunk_text


def test_empty_text_returns_empty_list() -> None:
    # Verifies blank documents do not create empty chunks.
    assert chunk_text("") == []
    assert chunk_text("   \n\n   ") == []


def test_short_text_returns_one_chunk() -> None:
    # Verifies small documents are preserved as a single clean chunk.
    chunks = chunk_text("  Short CV text.  ", chunk_size=100, overlap=20)

    assert chunks == ["Short CV text."]


def test_long_text_returns_multiple_chunks() -> None:
    # Verifies longer text is split into several chunks.
    text = " ".join(f"word{i}" for i in range(40))

    chunks = chunk_text(text, chunk_size=50, overlap=10)

    assert len(chunks) > 1


def test_chunk_size_limit_is_respected() -> None:
    # Verifies every returned chunk stays within the configured size.
    text = " ".join(f"word{i}" for i in range(40))

    chunks = chunk_text(text, chunk_size=50, overlap=10)

    assert all(len(chunk) <= 50 for chunk in chunks)


def test_overlap_behavior_repeats_boundary_words() -> None:
    # Verifies overlap keeps a small amount of context between adjacent chunks.
    text = " ".join(f"word{i}" for i in range(40))

    chunks = chunk_text(text, chunk_size=50, overlap=10)

    assert chunks[0].endswith("word7")
    assert chunks[1].startswith("word7 ")


def test_paragraph_and_newline_boundaries_are_preferred() -> None:
    # Verifies paragraph boundaries are preferred over arbitrary character cuts.
    text = (
        "First paragraph has FastAPI and SQL.\n\n"
        "Second paragraph has Docker and Git.\n\n"
        "Third paragraph has communication."
    )

    chunks = chunk_text(text, chunk_size=60, overlap=10)

    assert chunks == [
        "First paragraph has FastAPI and SQL.",
        "Second paragraph has Docker and Git.",
        "Third paragraph has communication.",
    ]


def test_chunks_do_not_start_with_broken_words_when_avoidable() -> None:
    # Verifies word separators prevent avoidable broken-word chunk starts.
    text = "alpha beta gamma delta epsilon zeta eta theta iota kappa lambda mu"
    expected_word_starts = {"alpha", "delta", "eta", "kappa"}

    chunks = chunk_text(text, chunk_size=25, overlap=5)
    actual_word_starts = {chunk.split(maxsplit=1)[0] for chunk in chunks}

    assert actual_word_starts == expected_word_starts


@pytest.mark.parametrize("chunk_size", [0, -1])
def test_invalid_chunk_size_raises_value_error(chunk_size: int) -> None:
    # Verifies chunk_size must be positive.
    with pytest.raises(ValueError, match="chunk_size must be greater than zero"):
        chunk_text("content", chunk_size=chunk_size)


@pytest.mark.parametrize("overlap", [-1, 10])
def test_invalid_overlap_raises_value_error(overlap: int) -> None:
    # Verifies overlap cannot be negative or as large as the chunk size.
    expected_message = (
        "overlap cannot be negative"
        if overlap < 0
        else "overlap must be smaller than chunk_size"
    )

    with pytest.raises(ValueError, match=expected_message):
        chunk_text("content", chunk_size=10, overlap=overlap)
