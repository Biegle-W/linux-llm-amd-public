"""Quant quality suite: 54 auto-graded items. Shared by the runner (prompts) and grader (keys)."""

MATH_SUFFIX = "\n\nShow brief working, then give the final answer alone on the last line as: ANSWER: <value>"
MATH = [
    ("m01", "Pencils cost $0.75 for 3 and pens cost $1.20 each. Maria buys 12 pencils and 5 pens and pays with a $20 bill. How much change does she get, in dollars?", ["11"]),
    ("m02", "A train leaves at 09:40 and travels 210 km at a constant 84 km/h. At what time does it arrive? Give HH:MM in 24-hour time.", ["12:10"]),
    ("m03", "What is the sum of all positive integers less than 100 that are divisible by 3 or by 5?", ["2318"]),
    ("m04", "How many trailing zeros does 125! (125 factorial) have?", ["31"]),
    ("m05", "A rectangle has perimeter 46 and diagonal 17. What is its area?", ["120"]),
    ("m06", "$5000 is invested at 4% interest compounded annually. What is the balance after 3 years, to the cent?", ["5624.32"]),
    ("m07", "A committee of 3 is chosen from 8 people, but two particular people refuse to serve together. How many different committees are possible?", ["50"]),
    ("m08", "Two fair six-sided dice are rolled. What is the probability that the sum is 8? Give a reduced fraction.", ["5/36"]),
    ("m09", "Solve for x: 3(x - 4) + 2 = 5x - 18", ["4"]),
    ("m10", "Pipe A fills a tank in 6 hours, pipe B fills it in 9 hours, and drain C empties a full tank in 12 hours. With all three open on an empty tank, how many hours until it is full? Give an exact reduced fraction.", ["36/7"]),
    ("m11", "What is 17^4 mod 23?", ["8"]),
    ("m12", "A student scores 82, 91 and 77 on three tests weighted 30%, 50% and 20% respectively. What is the weighted average?", ["85.5"]),
    ("m13", "A shirt is marked up 40% over cost and then sold at 25% off the marked price. What is the profit as a percent of cost? Give just the number.", ["5"]),
    ("m14", "The interior angles of a convex polygon sum to 1980 degrees. How many sides does it have?", ["13"]),
    ("m15", "In a class, 18 students play soccer, 15 play basketball, 7 play both, and 6 play neither. How many students are in the class?", ["32"]),
    ("m16", "With F(1) = F(2) = 1 and F(n) = F(n-1) + F(n-2), what is F(30)?", ["832040"]),
    ("m17", "Convert the binary number 101101101 to decimal.", ["365"]),
    ("m18", "What is the least common multiple of 84 and 120?", ["840"]),
]

CODE_SUFFIX = "\n\nReply with a single Python code block containing only the implementation (no tests, no input())."
CODE = [
    ("c01", "Write a Python function is_balanced(s) that returns True if the brackets (), [] and {} in string s are balanced and properly nested, ignoring all other characters.",
     "assert is_balanced('a(b[c]{d}e)f')\nassert not is_balanced('(]')\nassert not is_balanced('([)]')\nassert is_balanced('')\nassert not is_balanced('((')\nassert is_balanced('x{[()()]}')"),
    ("c02", "Write a Python function merge_intervals(intervals) that takes a list of [start, end] pairs and returns a new list of merged, non-overlapping intervals sorted by start. Touching intervals like [1,3] and [3,5] merge.",
     "assert merge_intervals([[1,3],[2,6],[8,10],[15,18]])==[[1,6],[8,10],[15,18]]\nassert merge_intervals([[1,4],[4,5]])==[[1,5]]\nassert merge_intervals([])==[]\nassert merge_intervals([[5,7],[1,2],[2,3]])==[[1,3],[5,7]]\nassert merge_intervals([[1,10],[2,3]])==[[1,10]]"),
    ("c03", "Write a Python function roman_to_int(s) that converts a Roman numeral string (1 to 3999) to an integer.",
     "assert roman_to_int('III')==3\nassert roman_to_int('LVIII')==58\nassert roman_to_int('MCMXCIV')==1994\nassert roman_to_int('MMMCMXCIX')==3999\nassert roman_to_int('XLIV')==44"),
    ("c04", "Write a Python function longest_common_prefix(strs) that returns the longest common prefix string of a list of strings ('' if none or if the list is empty).",
     "assert longest_common_prefix(['flower','flow','flight'])=='fl'\nassert longest_common_prefix(['dog','racecar','car'])==''\nassert longest_common_prefix([])==''\nassert longest_common_prefix(['abc'])=='abc'\nassert longest_common_prefix(['ab','a'])=='a'"),
    ("c05", "Write a Python function run_length_encode(s) that returns the run-length encoding of s as character followed by count, e.g. 'aaabcc' -> 'a3b1c2'. An empty string returns ''.",
     "assert run_length_encode('aaabcc')=='a3b1c2'\nassert run_length_encode('')==''\nassert run_length_encode('a')=='a1'\nassert run_length_encode('aaaaaaaaaaaa')=='a12'\nassert run_length_encode('abab')=='a1b1a1b1'"),
    ("c06", "Write a Python function top_k_frequent(words, k) that returns the k most frequent words, sorted by frequency descending, ties broken alphabetically ascending.",
     "assert top_k_frequent(['i','love','leetcode','i','love','coding'],2)==['i','love']\nassert top_k_frequent(['the','day','is','sunny','the','the','the','sunny','is','is'],4)==['the','is','sunny','day']\nassert top_k_frequent(['b','a','c'],2)==['a','b']"),
    ("c07", "Write a Python function spiral_order(matrix) that returns the elements of a 2D list in clockwise spiral order starting from the top-left. An empty matrix returns [].",
     "assert spiral_order([[1,2,3],[4,5,6],[7,8,9]])==[1,2,3,6,9,8,7,4,5]\nassert spiral_order([[1,2,3,4],[5,6,7,8],[9,10,11,12]])==[1,2,3,4,8,12,11,10,9,5,6,7]\nassert spiral_order([])==[]\nassert spiral_order([[1],[2],[3]])==[1,2,3]\nassert spiral_order([[1,2]])==[1,2]"),
    ("c08", "Write a Python class LRUCache with __init__(self, capacity), get(self, key) returning the value or -1 if absent, and put(self, key, value). When over capacity, evict the least recently used key. Both get and put count as use.",
     "c=LRUCache(2)\nc.put(1,1);c.put(2,2)\nassert c.get(1)==1\nc.put(3,3)\nassert c.get(2)==-1\nc.put(4,4)\nassert c.get(1)==-1\nassert c.get(3)==3\nassert c.get(4)==4\nd=LRUCache(1);d.put(1,1);d.put(1,5);assert d.get(1)==5;d.put(2,2);assert d.get(1)==-1"),
    ("c09", "Write a Python function parse_duration(s) that converts strings like '1h30m15s', '45m', '2h', '10s' or '1h5s' (hours, minutes, seconds, each optional but in that order) to a total number of seconds as an int.",
     "assert parse_duration('1h30m15s')==5415\nassert parse_duration('45m')==2700\nassert parse_duration('2h')==7200\nassert parse_duration('10s')==10\nassert parse_duration('1h5s')==3605\nassert parse_duration('12m3s')==723"),
    ("c10", "Write a Python function count_islands(grid) where grid is a list of lists of '1' (land) and '0' (water) strings; return the number of islands using 4-directional connectivity. Do not modify the input.",
     "g=[['1','1','0','0','0'],['1','1','0','0','0'],['0','0','1','0','0'],['0','0','0','1','1']]\nimport copy;h=copy.deepcopy(g)\nassert count_islands(g)==3\nassert g==h\nassert count_islands([])==0\nassert count_islands([['1','0','1'],['0','1','0'],['1','0','1']])==5\nassert count_islands([['1','1','1'],['1','0','1'],['1','1','1']])==1"),
    ("c11", "Write a Python function next_permutation(nums) that returns (as a new list) the next lexicographically greater permutation of the integer list nums; if none exists, return the list sorted ascending.",
     "assert next_permutation([1,2,3])==[1,3,2]\nassert next_permutation([3,2,1])==[1,2,3]\nassert next_permutation([1,1,5])==[1,5,1]\nassert next_permutation([1,3,2])==[2,1,3]\nassert next_permutation([2,3,1])==[3,1,2]"),
    ("c12", "Write a Python function eval_rpn(tokens) that evaluates a list of Reverse Polish Notation tokens with integers and the operators + - * /, where division truncates toward zero.",
     "assert eval_rpn(['2','1','+','3','*'])==9\nassert eval_rpn(['4','13','5','/','+'])==6\nassert eval_rpn(['10','6','9','3','+','-11','*','/','*','17','+','5','+'])==22\nassert eval_rpn(['7','-2','/'])==-3"),
]

SHORT_SUFFIX = " Answer with just the answer, no explanation."
KNOW = [
    ("k01", "What is the chemical symbol for tungsten?", r"^\W*W\W*$"),
    ("k02", "Who wrote the novel 'One Hundred Years of Solitude'?", r"m[aá]rquez"),
    ("k03", "What is the worst-case time complexity of binary search on a sorted array of n elements?", r"log"),
    ("k04", "In what year did the Berlin Wall fall?", r"\b1989\b"),
    ("k05", "Which gas do plants take in from the air for photosynthesis?", r"carbon dioxide|co2|co₂"),
    ("k06", "All bloops are razzies and all razzies are lazzies. Are all bloops definitely lazzies? Answer yes or no.", r"^\W*yes\b"),
    ("k07", "If 5 machines take 5 minutes to make 5 widgets, how many minutes would 100 machines take to make 100 widgets?", r"^\D*\b5\b(?!\d)"),
    ("k08", "A bat and a ball cost $1.10 in total. The bat costs $1.00 more than the ball. How many cents does the ball cost?", r"^\D*\b5\b(?!\d)"),
    ("k09", "How many times does the letter s appear in the word 'mississippi'?", r"^\D*\b4\b|four"),
    ("k10", "What is the capital city of Canada?", r"ottawa"),
    ("k11", "Which chemical element has atomic number 26?", r"iron|\bfe\b"),
    ("k12", "Sally has 3 brothers. Each of her brothers has 2 sisters. How many sisters does Sally have?", r"^\D*\b1\b|one"),
    ("k13", "What day of the week was 1 January 2000?", r"saturday"),
    ("k14", "In SQL, which clause filters groups after aggregation?", r"having"),
]

FORMAT = [
    ("f01", "Output only a JSON object (no code fence, no other text) describing a fictional cat with keys: name (string), age (integer), tags (array of exactly 3 lowercase strings)."),
    ("f02", "Write exactly 3 bullet points about the benefits of exercise. Each line must start with '- '. Output nothing else."),
    ("f03", "Reply with the word 'banana' spelled backwards in uppercase letters, and nothing else."),
    ("f04", "List the first five prime numbers separated by commas with no spaces. Output nothing else."),
    ("f05", "Translate 'thank you very much' into Spanish. Reply in lowercase with no punctuation and nothing else."),
    ("f06", "Sort these words alphabetically and output them on one line separated by single spaces, nothing else: pear apple mango banana cherry"),
]

WEATHER = {"type": "function", "function": {"name": "get_weather", "description": "Get the current weather for a city",
           "parameters": {"type": "object", "properties": {"city": {"type": "string"}, "unit": {"type": "string", "enum": ["celsius", "fahrenheit"]}}, "required": ["city", "unit"]}}}
FLIGHTS = {"type": "function", "function": {"name": "search_flights", "description": "Search flights between two airports/cities on a date (YYYY-MM-DD)",
           "parameters": {"type": "object", "properties": {"origin": {"type": "string"}, "destination": {"type": "string"}, "date": {"type": "string"}}, "required": ["origin", "destination", "date"]}}}
HOTEL = {"type": "function", "function": {"name": "book_hotel", "description": "Book a hotel room in a city",
         "parameters": {"type": "object", "properties": {"city": {"type": "string"}, "nights": {"type": "integer"}}, "required": ["city", "nights"]}}}
CALC = {"type": "function", "function": {"name": "calculator", "description": "Evaluate an arithmetic expression exactly",
        "parameters": {"type": "object", "properties": {"expression": {"type": "string"}}, "required": ["expression"]}}}
STOCK = {"type": "function", "function": {"name": "get_stock_price", "description": "Get the latest stock price for a ticker symbol",
         "parameters": {"type": "object", "properties": {"ticker": {"type": "string"}}, "required": ["ticker"]}}}

TOOLS = [
    ("t01", [{"role": "user", "content": "What's the weather in Tokyo right now? Use celsius."}], [WEATHER]),
    ("t02", [{"role": "user", "content": "Find me flights from Boston to Denver on 2026-12-03."}], [FLIGHTS, HOTEL]),
    ("t03", [{"role": "user", "content": "Use the calculator to compute 1234 * 5678."}], [CALC, WEATHER]),
    ("t04", [{"role": "user", "content": "What is Nvidia's stock price right now?"},
             {"role": "assistant", "content": "", "tool_calls": [{"id": "call_1", "type": "function", "function": {"name": "get_stock_price", "arguments": "{\"ticker\": \"NVDA\"}"}}]},
             {"role": "tool", "tool_call_id": "call_1", "content": "{\"ticker\": \"NVDA\", \"price\": 187.42, \"currency\": \"USD\"}"}], [STOCK]),
]


def requests():
    """(id, category, body-without-model) for every item."""
    out = []
    for i, q, _ in MATH:
        out.append((i, "math", {"messages": [{"role": "user", "content": q + MATH_SUFFIX}], "max_tokens": 700}))
    for i, q, _ in CODE:
        out.append((i, "code", {"messages": [{"role": "user", "content": q + CODE_SUFFIX}], "max_tokens": 900}))
    for i, q, _ in KNOW:
        out.append((i, "know", {"messages": [{"role": "user", "content": q + SHORT_SUFFIX}], "max_tokens": 60}))
    for i, q in FORMAT:
        out.append((i, "format", {"messages": [{"role": "user", "content": q}], "max_tokens": 200}))
    for i, msgs, tools in TOOLS:
        out.append((i, "tool", {"messages": msgs, "tools": tools, "max_tokens": 300}))
    return out
