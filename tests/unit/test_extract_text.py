from types import SimpleNamespace as NS

import pytest

from adapters.anthropic_adapter import extract_text


def msg(*blocks, stop="end_turn"):
    return NS(content=list(blocks), stop_reason=stop)


def test_skips_thinking_blocks():
    m = msg(NS(type="thinking", thinking="hmm"), NS(type="text", text="Answer: 42"))
    assert extract_text(m) == "Answer: 42"


def test_joins_multiple_text_blocks():
    assert extract_text(msg(NS(type="text", text="a"), NS(type="text", text="b"))) == "ab"


def test_no_text_block_raises_clear_error():
    with pytest.raises(ValueError, match="no text block"):
        extract_text(msg(NS(type="thinking", thinking="x"), stop="max_tokens"))
