from langchain_text_splitters import RecursiveCharacterTextSplitter


DEFAULT_CHUNK_SIZE = 500
DEFAULT_OVERLAP = 100
DEFAULT_SEPARATORS = ["\n\n", "\n", ". ", " ", ""]


def chunk_text(
    text: str,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    overlap: int = DEFAULT_OVERLAP,
) -> list[str]:
    if chunk_size <= 0:
        raise ValueError("chunk_size must be greater than zero.")
    if overlap < 0:
        raise ValueError("overlap cannot be negative.")
    if overlap >= chunk_size:
        raise ValueError("overlap must be smaller than chunk_size.")

    clean_text = text.strip()
    if not clean_text:
        return []

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=overlap,
        separators=DEFAULT_SEPARATORS,
        keep_separator=False,
    )

    return [chunk.strip() for chunk in splitter.split_text(clean_text) if chunk.strip()]
