"""Optional-<think> reasoning parser for Ripple-65B on vLLM dev229.

Ripple answers directly by default and only sometimes opens with a <think>...</think> block
(upstream vLLM's Ripple parser, PR #65745, uses the newer parser engine that dev229 lacks).
dev229's qwen3/olmo3 parsers assume the output starts inside reasoning, so plain answers
and tool calls were swallowed as reasoning. This parser decides from the first
non-whitespace text:
  - output starting with <think>: text up to </think> is reasoning, the rest is content;
  - anything else: all content, reasoning ends immediately (so tool parsing starts at once).
Text-based: Ripple's tokenizer has no single <think> token. One instance per request.
"""
from collections.abc import Sequence

from vllm.entrypoints.generate.base.protocol import DeltaMessage
from vllm.reasoning import ReasoningParser

START, END = "<think>", "</think>"


def _hold_back(text: str, marker: str) -> int:
    """Length of the longest suffix of text that is a proper prefix of marker."""
    for n in range(min(len(text), len(marker) - 1), 0, -1):
        if marker.startswith(text[-n:]):
            return n
    return 0


class RippleOptionalThinkParser(ReasoningParser):
    def __init__(self, tokenizer, *args, **kwargs):
        super().__init__(tokenizer, *args, **kwargs)
        self.mode = "undecided"      # undecided -> thinking -> content, or undecided -> content
        self.reasoning_sent = 0      # characters of reasoning already emitted
        self.content_ids_all = True  # no-think output: every token is content

    @property
    def reasoning_start_str(self) -> str:
        return START

    @property
    def reasoning_end_str(self) -> str:
        return END

    def is_reasoning_end(self, input_ids: Sequence[int]) -> bool:
        # State-based: also called with the prompt ids before generation (mode undecided -> False).
        return self.mode == "content"

    def extract_content_ids(self, input_ids: list[int]) -> list[int]:
        return list(input_ids) if self.content_ids_all else []

    def extract_reasoning(self, model_output: str, request) -> tuple[str | None, str | None]:
        s = model_output.lstrip()
        if s.startswith(START):
            body = s[len(START):]
            if END in body:
                reasoning, content = body.split(END, 1)
                return reasoning.strip("\n") or None, content.lstrip("\n") or None
            return body.strip("\n") or None, None
        return None, model_output

    def extract_reasoning_streaming(self, previous_text, current_text, delta_text,
                                    previous_token_ids, current_token_ids, delta_token_ids):
        lead = len(current_text) - len(current_text.lstrip())
        s = current_text[lead:]
        if self.mode == "undecided":
            if not s or START.startswith(s):
                return None                      # wait: whitespace or a partial "<think>"
            if not s.startswith(START):
                self.mode = "content"
                return DeltaMessage(content=current_text)
            self.mode = "thinking"
            self.content_ids_all = False
        if self.mode == "thinking":
            body = s[len(START):]
            if END in body:
                reasoning, content = body.split(END, 1)
                new = reasoning[self.reasoning_sent:].rstrip("\n") if self.reasoning_sent < len(reasoning) else ""
                if self.reasoning_sent == 0:
                    new = new.lstrip("\n")
                self.mode = "content"
                content = content.lstrip("\n")
                return DeltaMessage(reasoning=new or None, content=content or None)
            safe = len(body) - _hold_back(body, END)
            while safe > self.reasoning_sent and body[safe - 1] == "\n":
                safe -= 1  # a newline may be the one right before </think>
            new = body[self.reasoning_sent:safe]
            if self.reasoning_sent == 0:
                stripped = new.lstrip("\n")
                self.reasoning_sent += len(new) - len(stripped)
                new = stripped
            self.reasoning_sent += len(new)
            return DeltaMessage(reasoning=new) if new else None
        return DeltaMessage(content=delta_text)


def register():
    from vllm.reasoning import ReasoningParserManager
    ReasoningParserManager._register_module(RippleOptionalThinkParser, "ripple_optional_think")


# Imported by --reasoning-parser-plugin: register on import.
register()
