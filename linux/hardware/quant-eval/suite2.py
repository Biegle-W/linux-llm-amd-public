"""Harder DeepSeek quant suite (November 8): knowledge, trick reasoning, harder code, long context, multi-step tools, format.
Shared by run_suite.py (via SUITE=suite2) and grade2.py."""
import random

SHORT = " Answer with just the answer, no explanation."
CODE_SUFFIX = "\n\nReply with a single Python code block containing only the implementation (no tests, no input())."

KNOW = [
    ("k01", "What is the capital of Australia?", r"canberra"),
    ("k02", "What is the chemical symbol for tungsten?", r"^\W*W\b"),
    ("k03", "Who wrote the novel 'Crime and Punishment'?", r"dosto[ye]+vsk"),
    ("k04", "What is the largest moon of Saturn?", r"titan"),
    ("k05", "In what year did the Berlin Wall fall?", r"1989"),
    ("k06", "What is the SI unit of electrical resistance?", r"ohm|Ω"),
    ("k07", "Who painted 'The Persistence of Memory'?", r"dal[ií]"),
    ("k08", "What is the smallest prime number greater than 100?", r"\b101\b"),
    ("k09", "Which element has atomic number 79?", r"gold|\bau\b"),
    ("k10", "What is the longest river in South America?", r"amazon"),
    ("k11", "Which language has the most native speakers in the world?", r"mandarin|chinese"),
    ("k12", "Who developed the general theory of relativity?", r"einstein"),
    ("k13", "What is the capital of Canada?", r"ottawa"),
    ("k14", "What is the hardest naturally occurring mineral?", r"diamond"),
    ("k15", "Which planet has the Great Red Spot?", r"jupiter"),
    ("k16", "Who composed 'The Four Seasons'?", r"vivaldi"),
    ("k17", "What is the currency of Japan?", r"\byen\b|¥"),
    ("k18", "Who was the first person to walk on the Moon?", r"armstrong"),
    ("k19", "Which organelle produces most of a cell's ATP?", r"mitochondri"),
    ("k20", "What is the capital of Turkey?", r"ankara"),
    ("k21", "Who wrote 'On the Origin of Species'?", r"darwin"),
    ("k22", "What is the most abundant gas in Earth's atmosphere?", r"nitrogen|\bn2\b|n₂"),
    ("k23", "In what year did the French Revolution begin?", r"1789"),
    ("k24", "Who wrote 'Pride and Prejudice'?", r"austen"),
    ("k25", "What is the chemical formula of table salt?", r"nacl"),
    ("k26", "In which museum is the Mona Lisa displayed?", r"louvre"),
    ("k27", "Which element has the chemical symbol K?", r"potassium"),
    ("k28", "How many bones are in the adult human body?", r"\b206\b"),
    ("k29", "Who proposed the heliocentric model in 'De revolutionibus' (1543)?", r"copernic"),
    ("k30", "What is the capital of Brazil?", r"bras[ií]lia"),
]

REASON = [
    ("r01", "If 5 machines take 5 minutes to make 5 widgets, how many minutes would 100 machines take to make 100 widgets?", r"^\W*5\b"),
    ("r02", "A patch of lily pads doubles in size every day and covers the whole lake in 48 days. On what day did it cover half the lake?", r"\b47\b"),
    ("r03", "A farmer has 17 sheep and all but 9 die. How many sheep are left?", r"^\W*9\b"),
    ("r04", "How many times does the letter 'r' appear in the word 'strawberry'?", r"^\W*3\b|three"),
    ("r05", "Alice is older than Bob. Carol is younger than Bob. Dave is older than Alice. Who is the youngest?", r"carol"),
    ("r06", "What day of the week was January 1, 2000?", r"saturday"),
    ("r07", "A clock shows 3:15. What is the angle in degrees between the hour and minute hands?", r"7\.5"),
    ("r08", "Mary's father has five daughters: Nana, Nene, Nini and Nono. What is the fifth daughter's name?", r"mary"),
    ("r09", "How many words are in this sentence: 'The quick brown fox jumps over the lazy dog'?", r"^\W*9\b|nine"),
    ("r10", "Spell the word 'necessary' backwards.", r"yrassecen"),
    ("r11", "If today is Wednesday, what day of the week will it be 100 days from now?", r"friday"),
    ("r12", "I am thinking of a number. Double it, add 6, halve the result, then subtract the original number. What is the result?", r"^\W*3\b|three"),
]

CODE = [
    ("c01", "Write a Python class LRUCache with __init__(self, capacity), get(self, key) returning -1 when absent, and put(self, key, value). When over capacity, evict the least recently used key; both get and put count as use.",
     "c=LRUCache(2);c.put(1,1);c.put(2,2);assert c.get(1)==1;c.put(3,3);assert c.get(2)==-1;c.put(4,4);assert c.get(1)==-1;assert c.get(3)==3;assert c.get(4)==4\nc=LRUCache(1);c.put(1,1);c.put(1,5);assert c.get(1)==5;c.put(2,2);assert c.get(1)==-1"),
    ("c02", "Write a Python function merge_intervals(intervals) that takes a list of [start, end] lists and returns the merged, sorted list of [start, end] lists. Touching intervals like [1,2] and [2,3] merge.",
     "assert merge_intervals([[1,3],[2,6],[8,10],[15,18]])==[[1,6],[8,10],[15,18]]\nassert merge_intervals([[1,4],[4,5]])==[[1,5]]\nassert merge_intervals([[5,7],[1,2]])==[[1,2],[5,7]]\nassert merge_intervals([])==[]\nassert merge_intervals([[1,10],[2,3],[4,5]])==[[1,10]]"),
    ("c03", "Write a Python function eval_expr(s) that evaluates an arithmetic expression string containing non-negative integers, + - * /, parentheses, spaces and unary minus, with normal precedence, where / is true division. Do not use eval, exec or compile.",
     "import builtins\n_e=builtins.eval\nbuiltins.eval=None;builtins.exec=None\nassert eval_expr('2+3*4')==14\nassert eval_expr('(2+3)*4')==20\nassert abs(eval_expr('10/4')-2.5)<1e-9\nassert eval_expr('-3+5')==2\nassert eval_expr('2*(3+(4-1))*2')==24\nassert eval_expr(' 7 - 2 - 1 ')==4\nassert eval_expr('-(2+3)*2')==-10\nassert abs(eval_expr('8/2/2')-2)<1e-9"),
    ("c04", "Write a Python function topo_sort(n, edges) for nodes 0..n-1 and a list of (u, v) edges meaning u must come before v. Return a list ordering all nodes, or None if there is a cycle.",
     "def ok(n,e,o):\n    return o is not None and sorted(o)==list(range(n)) and all(o.index(u)<o.index(v) for u,v in e)\nassert ok(4,[(0,1),(1,2),(0,3),(3,2)],topo_sort(4,[(0,1),(1,2),(0,3),(3,2)]))\nassert topo_sort(3,[(0,1),(1,2),(2,0)]) is None\nassert ok(3,[],topo_sort(3,[]))\nassert topo_sort(2,[(1,1)]) is None\nassert ok(5,[(4,0),(3,1),(2,4)],topo_sort(5,[(4,0),(3,1),(2,4)]))"),
    ("c05", "Write two Python functions: to_roman(n) converting an integer 1..3999 to a Roman numeral string, and from_roman(s) converting a Roman numeral string back to an integer.",
     "for n,s in [(1,'I'),(4,'IV'),(9,'IX'),(14,'XIV'),(40,'XL'),(90,'XC'),(400,'CD'),(1994,'MCMXCIV'),(2024,'MMXXIV'),(3999,'MMMCMXCIX')]:\n    assert to_roman(n)==s,(n,to_roman(n))\n    assert from_roman(s)==n\nassert all(from_roman(to_roman(i))==i for i in range(1,4000))"),
    ("c06", "Write a Python function lcs_length(a, b) returning the length of the longest common subsequence of strings a and b.",
     "assert lcs_length('ABCBDAB','BDCABA')==4\nassert lcs_length('','abc')==0\nassert lcs_length('abc','abc')==3\nassert lcs_length('AGGTAB','GXTXAYB')==4\nassert lcs_length('abc','def')==0"),
    ("c07", "Write a Python function dijkstra(graph, src) where graph maps each node to a list of (neighbor, weight) pairs with non-negative weights. Return a dict of shortest distances from src to every reachable node (including src at 0).",
     "g={'A':[('B',1),('C',4)],'B':[('C',2),('D',5)],'C':[('D',1)],'D':[],'E':[('A',1)]}\nassert dijkstra(g,'A')=={'A':0,'B':1,'C':3,'D':4}\nassert dijkstra(g,'D')=={'D':0}\nassert dijkstra({1:[(2,7),(3,9),(6,14)],2:[(1,7),(3,10),(4,15)],3:[(1,9),(2,10),(4,11),(6,2)],4:[(2,15),(3,11),(5,6)],5:[(4,6),(6,9)],6:[(1,14),(3,2),(5,9)]},1)=={1:0,2:7,3:9,4:20,5:20,6:11}"),
    ("c08", "Write a Python function is_valid_sudoku(board) where board is a list of 9 strings of length 9 using digits 1-9 and '.' for empty cells. Return True if no row, column or 3x3 box contains a repeated digit (the board need not be solvable).",
     "b=['53..7....','6..195...','.98....6.','8...6...3','4..8.3..1','7...2...6','.6....28.','...419..5','....8..79']\nassert is_valid_sudoku(b) is True\nb2=list(b);b2[0]='83..7....'\nassert is_valid_sudoku(b2) is False\nb3=list(b);b3[1]='6..195..5'\nassert is_valid_sudoku(b3) is False\nb4=list(b);b4[2]='598....6.'\nassert is_valid_sudoku(b4) is False\nassert is_valid_sudoku(['.'*9]*9) is True"),
    ("c09", "Write a Python function word_wrap(text, width) that greedily packs whitespace-separated words into lines joined by single spaces, each at most width characters, and returns the list of lines. A word longer than width goes on its own line unbroken.",
     "assert word_wrap('the quick brown fox jumps over the lazy dog',10)==['the quick','brown fox','jumps over','the lazy','dog']\nassert word_wrap('',5)==[]\nassert word_wrap('a supercalifragilistic b',5)==['a','supercalifragilistic','b']\nassert word_wrap('  hello   world  ',11)==['hello world']"),
    ("c10", "Write a Python function next_permutation(nums) that returns a new list with the next lexicographically greater permutation of nums, or the ascending sorted list if nums is the last permutation. Do not modify the input.",
     "assert next_permutation([1,2,3])==[1,3,2]\nassert next_permutation([3,2,1])==[1,2,3]\nassert next_permutation([1,1,5])==[1,5,1]\nassert next_permutation([1,3,2])==[2,1,3]\nx=[2,3,1];assert next_permutation(x)==[3,1,2] and x==[2,3,1]\nassert next_permutation([1])==[1]"),
]

FORMAT = [
    ("f01", "Output a JSON array of the first five positive square numbers and nothing else.", "json", [1, 4, 9, 16, 25]),
    ("f02", "List the eight planets of the solar system in order from the Sun, comma-separated with no spaces, and output nothing else.", "exact", "Mercury,Venus,Earth,Mars,Jupiter,Saturn,Uranus,Neptune"),
    ("f03", "Output a Markdown table with columns Name and Age and two rows: Ann 30, Bo 25. Output only the table.", "table", None),
    ("f04", "Reply with the word done in uppercase and nothing else.", "exact", "DONE"),
]


def _doc():
    rnd = random.Random(20261108)
    first = ["Ada", "Bram", "Cleo", "Dmitri", "Esme", "Farid", "Greta", "Hugo", "Ines", "Jonas", "Kaia", "Lucas", "Mira", "Nils", "Oona", "Pavel", "Quinn", "Rosa", "Soren", "Talia"]
    last = ["Abbott", "Brandt", "Castillo", "Dorsey", "Eklund", "Fischer", "Gallo", "Hart", "Ivanova", "Jensen", "Kowalski", "Lindqvist", "Moreau", "Novak", "Okafor", "Petrov", "Quill", "Romano", "Sato", "Tanaka"]
    depts = ["Logistics", "Finance", "Research", "Support", "Design", "Legal", "Sales", "Security"]
    cities = ["Lyon", "Porto", "Graz", "Tartu", "Bergen", "Ghent", "Brno", "Turku", "Aarhus", "Cork"]
    names = rnd.sample([f"{f} {l}" for f in first for l in last], 140)
    lines = []
    for i, n in enumerate(names):
        lines.append(f"Record {i + 1:03d}: {n} works in {rnd.choice(depts)}, joined in {rnd.randint(2004, 2023)}, and is based in the {rnd.choice(cities)} office. "
                     f"Their badge was last renewed in {rnd.choice(['March', 'June', 'September', 'December'])}.")
    lead, joiner = names[37], names[118]
    lines[37] = f"Record 038: {lead} works in Research, joined in 2011, and is based in the Tartu office. Their badge was last renewed in June."
    lines[118] = f"Record 119: {joiner} works in Legal, joined in 2016, and is based in the Ghent office. Their badge was last renewed in March."
    lines.insert(71, "Facilities note: the server room vault access code was changed to 4719-ALPHA on the first Monday of the quarter.")
    lines.insert(102, f"Org note: the new Quantum team is led by {lead}.")
    doc = "COMPANY STAFF REGISTER\n\n" + "\n".join(lines)
    qs = [
        ("L1", "What is the server room vault access code?", r"4719-?ALPHA"),
        ("L2", "In which city's office is the leader of the Quantum team based?", r"tartu"),
        ("L3", f"In what year did {joiner} join, and which department do they work in?", r"2016.*legal|legal.*2016"),
    ]
    return doc, qs


DOC, LONG = _doc()

T = lambda name, desc, props, req: {"type": "function", "function": {"name": name, "description": desc, "parameters": {"type": "object", "properties": props, "required": req}}}
S = {"type": "string"}
READ = T("read_file", "Read a file in the repository", {"path": S}, ["path"])
WRITE = T("write_file", "Overwrite a file in the repository with new content", {"path": S, "content": S}, ["path", "content"])
TESTS = T("run_tests", "Run the test suite and return the output", {}, [])
WEATHER = T("get_weather", "Get current weather for a city", {"city": S}, ["city"])
CONVERT = T("convert_currency", "Convert an amount between currencies", {"amount": {"type": "number"}, "from_currency": S, "to_currency": S}, ["amount", "from_currency", "to_currency"])
HOTEL = T("book_hotel", "Book a hotel", {"city": S, "nights": {"type": "integer"}}, ["city", "nights"])
FLIGHT = T("search_flights", "Search flights", {"origin": S, "destination": S, "date": S}, ["origin", "destination", "date"])
SEARCH = T("search_docs", "Search the internal documentation", {"query": S}, ["query"])


def call(i, name, args):
    import json
    return {"id": i, "type": "function", "function": {"name": name, "arguments": json.dumps(args)}}


AGENT = [
    ("a01", [{"role": "user", "content": "The tests are failing. Please find and fix the bug."},
             {"role": "assistant", "content": "", "tool_calls": [call("c1", "run_tests", {})]},
             {"role": "tool", "tool_call_id": "c1", "content": "FAILED test_calc.py::test_add - assert add(2, 3) == 5, got -1\n1 failed, 4 passed"},
             {"role": "assistant", "content": "", "tool_calls": [call("c2", "read_file", {"path": "calc.py"})]},
             {"role": "tool", "tool_call_id": "c2", "content": "def add(a, b):\n    return a - b\n\n\ndef mul(a, b):\n    return a * b\n"}],
     [READ, WRITE, TESTS]),
    ("a02", [{"role": "user", "content": "What's the weather like in the capital of France?"}], [WEATHER, SEARCH]),
    ("a03", [{"role": "user", "content": "How much is 250 US dollars in euros?"},
             {"role": "assistant", "content": "", "tool_calls": [call("c1", "convert_currency", {"amount": 250, "from_currency": "USD", "to_currency": "EUR"})]},
             {"role": "tool", "tool_call_id": "c1", "content": "{\"amount\": 250, \"from\": \"USD\", \"to\": \"EUR\", \"result\": 231.75}"}],
     [CONVERT]),
    ("a04", [{"role": "user", "content": "Book me a hotel in Lisbon for 3 nights."}], [FLIGHT, HOTEL, WEATHER, SEARCH]),
    ("a05", [{"role": "user", "content": "The tests are failing. Please find and fix the bug."},
             {"role": "assistant", "content": "", "tool_calls": [call("c1", "run_tests", {})]},
             {"role": "tool", "tool_call_id": "c1", "content": "FAILED test_text.py::test_slug - assert slugify('Hello World') == 'hello-world', got 'hello_world'\n1 failed, 9 passed"}],
     [READ, WRITE, TESTS]),
]


def requests():
    out = []
    for i, q, _ in KNOW:
        out.append((i, "know", {"messages": [{"role": "user", "content": q + SHORT}], "max_tokens": 60}))
    for i, q, _ in REASON:
        out.append((i, "reason", {"messages": [{"role": "user", "content": q + SHORT}], "max_tokens": 60}))
    for i, q, _ in CODE:
        out.append((i, "code", {"messages": [{"role": "user", "content": q + CODE_SUFFIX}], "max_tokens": 1200}))
    for i, q, *_ in FORMAT:
        out.append((i, "format", {"messages": [{"role": "user", "content": q}], "max_tokens": 200}))
    for i, msgs, tools in AGENT:
        out.append((i, "agent", {"messages": msgs, "tools": tools, "max_tokens": 400}))
    for i, q, _ in LONG:
        out.append((i, "long", {"messages": [{"role": "user", "content": DOC + "\n\nUsing only the register above, answer: " + q + SHORT}], "max_tokens": 60}))
    return out
