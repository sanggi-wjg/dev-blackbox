def chunk_content(
    content: str,
    chunk_size: int = 2000,
    overlap_size: int = 400,
    split_separator: str = "\n\n",
) -> list[str]:
    content = content.strip()
    if not content:
        return []

    if len(content) <= chunk_size:
        return [content]

    sections = split_by_separator(content, split_separator)
    chunks: list[str] = []

    for section in sections:
        if len(section) <= chunk_size:
            chunks.append(section)
        else:
            chunks.extend(
                split_section(section, chunk_size, overlap_size),
            )

    return [chunk for chunk in chunks if chunk.strip()]


def split_by_separator(content: str, separator: str) -> list[str]:
    lines = content.split("\n")
    sections: list[str] = []
    current_lines: list[str] = []

    for line in lines:
        if line.startswith(separator) and current_lines:
            sections.append("\n".join(current_lines))
            current_lines = []
        current_lines.append(line)

    if current_lines:
        sections.append("\n".join(current_lines))

    return sections


def split_section(
    section: str,
    max_chunk_chars: int,
    overlap_chars: int,
) -> list[str]:
    """긴 섹션을 단락 → 줄 기준으로 재분할한다."""
    # 단락 기준 분할 시도
    paragraphs = section.split("\n\n")
    if len(paragraphs) > 1:
        return _merge_with_overlap(paragraphs, "\n\n", max_chunk_chars, overlap_chars)

    # 줄 기준 분할
    lines = section.split("\n")
    if len(lines) > 1:
        return _merge_with_overlap(lines, "\n", max_chunk_chars, overlap_chars)

    # 분할 불가능한 긴 텍스트 → 문자 단위 슬라이싱
    return _slice_by_chars(section, max_chunk_chars, overlap_chars)


def _merge_with_overlap(
    parts: list[str],
    separator: str,
    max_chunk_chars: int,
    overlap_chars: int,
) -> list[str]:
    """
    파트들을 max_chunk_chars 이내로 병합하고, 청크 간 overlap을 적용한다.
    """
    chunks: list[str] = []
    current_parts: list[str] = []
    current_len = 0

    for part in parts:
        part_len = len(part)
        added_len = part_len + (len(separator) if current_parts else 0)

        if current_len + added_len > max_chunk_chars and current_parts:
            chunks.append(separator.join(current_parts))
            # overlap: 뒤에서부터 overlap_chars만큼 유지
            overlap_parts: list[str] = []
            overlap_len = 0
            for p in reversed(current_parts):
                if overlap_len + len(p) > overlap_chars:
                    break
                overlap_parts.insert(0, p)
                overlap_len += len(p) + len(separator)
            current_parts = overlap_parts
            current_len = sum(len(p) for p in current_parts) + len(separator) * max(
                len(current_parts) - 1, 0
            )

        current_parts.append(part)
        current_len += added_len

    if current_parts:
        chunks.append(separator.join(current_parts))

    return chunks


def _slice_by_chars(
    text: str,
    max_chunk_chars: int,
    overlap_chars: int,
) -> list[str]:
    """문자 단위로 슬라이싱한다."""
    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = start + max_chunk_chars
        chunks.append(text[start:end])
        start = end - overlap_chars
    return chunks
