#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""文本分块。"""
import re
from typing import List


def chunk_text(text: str, max_chars: int = 900, overlap: int = 80) -> List[str]:
    text = (text or "").strip()
    if not text:
        return []
    if len(text) <= max_chars:
        return [text]

    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    chunks: List[str] = []
    buffer = ""

    def flush_buffer() -> None:
        nonlocal buffer
        if buffer.strip():
            chunks.append(buffer.strip())
        buffer = ""

    for para in paragraphs:
        if len(para) > max_chars:
            flush_buffer()
            start = 0
            while start < len(para):
                end = min(len(para), start + max_chars)
                chunks.append(para[start:end].strip())
                if end >= len(para):
                    break
                start = max(0, end - overlap)
            continue

        candidate = f"{buffer}\n\n{para}".strip() if buffer else para
        if len(candidate) <= max_chars:
            buffer = candidate
        else:
            flush_buffer()
            buffer = para
    flush_buffer()
    return chunks
