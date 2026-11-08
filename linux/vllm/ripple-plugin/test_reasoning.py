import sys
sys.path.insert(0, sys.argv[1])
from vllm_ripple.reasoning import RippleOptionalThinkParser as P

class Tok:
    def get_vocab(self): return {}
    vocab = {}

def run(chunks):
    p = P(Tok()); cur = ""; r = c = ""; ended_at = None
    for i, d in enumerate(chunks):
        prev, cur = cur, cur + d
        m = p.extract_reasoning_streaming(prev, cur, d, [], [], [])
        if m:
            r += m.reasoning or ""; c += m.content or ""
        if ended_at is None and p.is_reasoning_end([]):
            ended_at = i
            if i + 1 < len(chunks):  # after transition the serving layer streams content directly
                c += "".join(chunks[i + 1:]); break
    return r, c, ended_at

cases = {
  "plain": (["3", "91"], ("", "391")),
  "tool_no_think": (["\n<tool", "_call>\n{\"name\": \"read_file\"}", "\n</tool_call>"], ("", "\n<tool_call>\n{\"name\": \"read_file\"}\n</tool_call>")),
  "think_split": (["<th", "ink>\nadd", " them\n</th", "ink>\n391"], ("add them", "391")),
  "think_then_tool": (["<think>\nuse tool\n</think>\n", "<tool_call>{}</tool_call>"], ("use tool", "<tool_call>{}</tool_call>")),
  "leading_ws_plain": (["\n", "Hello"], ("", "\nHello")),
}
ok = True
for name, (chunks, want) in cases.items():
    r, c, e = run(chunks)
    good = (r, c) == want
    ok &= good
    print(("PASS" if good else "FAIL"), name, repr(r), repr(c), "ended_at", e)
p = P(Tok())
print("nonstream", p.extract_reasoning("<think>\nx\n</think>\n391", None), p.extract_reasoning("391", None))
print("prompt check before generation:", p.is_reasoning_end([1, 2, 3]))
sys.exit(0 if ok else 1)
