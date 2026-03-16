def chunk_work_log_content(content: str, chunk_size: int = 1000) -> list[str]:
    """업무 일지 마크다운 구조에 특화된 청킹.

    항목 단위로 분할하고, 섹션 헤더(### [...])를 각 청크에 주입한다.
    """
    content = content.strip()
    if not content:
        return []

    sections = _split_into_sections(content)

    # 섹션/항목 구조가 없는 단순 텍스트는 크기 기반 판단
    if len(sections) == 1 and not sections[0][0] and "\n- " not in content:
        if len(content) <= chunk_size:
            return [content]
    chunks: list[str] = []

    for header, body in sections:
        if not body.strip():
            continue

        items = _split_into_items(body)
        for item in items:
            chunk = f"{header}\n{item}" if header else item
            if len(chunk) <= chunk_size:
                chunks.append(chunk)
            else:
                # fallback: 문자 단위 분할 (헤더 길이를 고려)
                chunks.extend(_slice_by_chars(chunk, chunk_size, 0))

    return [chunk for chunk in chunks if chunk.strip()]


def _split_into_sections(content: str) -> list[tuple[str, str]]:
    """content를 (섹션 헤더, 섹션 본문) 쌍으로 분리한다."""
    lines = content.split("\n")
    sections: list[tuple[str, str]] = []
    current_header = ""
    current_body_lines: list[str] = []

    for line in lines:
        if line.startswith("### "):
            if current_body_lines or current_header:
                sections.append((current_header, "\n".join(current_body_lines)))
            current_header = line
            current_body_lines = []
        else:
            current_body_lines.append(line)

    if current_body_lines or current_header:
        sections.append((current_header, "\n".join(current_body_lines)))

    return sections


def _split_into_items(body: str) -> list[str]:
    """섹션 본문을 최상위 항목(- 로 시작) 단위로 분리한다.

    들여쓰기된 하위 항목(  - )은 상위 항목에 포함된다.
    """
    items: list[str] = []
    current_lines: list[str] = []

    for line in body.split("\n"):
        if line.startswith("- ") and current_lines:
            items.append("\n".join(current_lines))
            current_lines = []
        current_lines.append(line)

    if current_lines:
        item = "\n".join(current_lines)
        if item.strip():
            items.append(item)

    return items


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
