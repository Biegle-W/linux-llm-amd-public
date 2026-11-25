"""Tool schema conversion and grading from the public-suite references."""

import json
import re

from fast_amd.bfcl.openai_schema import convert_to_tool


class GraderDefect(ValueError):
    pass


def tool_schema(value):
    if isinstance(value, list):
        return [tool_schema(v) for v in value]
    if isinstance(value, dict):
        out = {}
        for k, v in value.items():
            if k in {'properties', '$defs', 'definitions'} and isinstance(v, dict):
                out[k] = {name: tool_schema(schema) for name, schema in v.items()}
            elif k in {'enum', 'default', 'examples'}:
                out[k] = v  # literal values, never schema-convert parameter names or enums
            else:
                out[k] = tool_schema(v)
        if 'type' in out:
            mapping = {'dict':'object','float':'number','int':'integer','str':'string','bool':'boolean','tuple':'array','list':'array'}
            t = out['type']
            if not isinstance(t,str) or t not in set(mapping) | {'object','number','integer','string','boolean','array','null'}:
                raise ValueError('Unknown/ambiguous tool schema type: ' + repr(t))
            out['type'] = mapping.get(t,t)
        return out
    return value


def typed_equal(a, b):
    if type(a) is not type(b): return False
    if isinstance(a, dict): return set(a) == set(b) and all(typed_equal(a[k], b[k]) for k in a)
    if isinstance(a, list): return len(a) == len(b) and all(typed_equal(x,y) for x,y in zip(a,b))
    return a == b


def validate_gold_tools(expected):
    if not isinstance(expected, list): raise GraderDefect('BFCL gold must be a list')
    for e in expected:
        if not isinstance(e, dict) or len(e) != 1: raise GraderDefect('invalid BFCL gold call')
        params = next(iter(e.values()))
        if not isinstance(params, dict) or any(not isinstance(v, list) or not v for v in params.values()):
            raise GraderDefect('invalid BFCL parameter alternatives')


def tool_match(calls, expected):
    validate_gold_tools(expected)
    if calls is None: calls = []
    if not isinstance(calls, list): return False
    actual = []
    for c in calls:
        try:
            f = c['function']; args = f['arguments']
            if isinstance(args, str): args = json.loads(args, parse_constant=lambda x: (_ for _ in ()).throw(ValueError('nonfinite JSON')))
            if not isinstance(args, dict) or not isinstance(f['name'], str): return False
            actual.append((f['name'], args))
        except (KeyError, TypeError, ValueError): return False
    if len(actual) != len(expected): return False
    def matches(a, e):
        name, params = next(iter(e.items()))
        if a[0] != name or set(a[1]) - set(params): return False
        return all((key not in a[1] and any(type(v) is str and v == '' for v in allowed)) or
                   (key in a[1] and any(typed_equal(a[1][key], v) for v in allowed))
                   for key, allowed in params.items())
    def search(i, remaining):
        if i == len(actual): return True
        return any(matches(actual[i], expected[j]) and search(i+1, remaining - {j}) for j in sorted(remaining))
    return search(0, set(range(len(expected))))


def normalize_name(name):
    return name.replace(".", "_")


def validate_tool_names(functions):
    seen = set()
    for function in functions:
        name = normalize_name(function["name"])
        if name in seen or not re.fullmatch(r"[a-zA-Z0-9_-]{1,64}", name):
            raise ValueError(f"Invalid or colliding tool name: {name!r}")
        seen.add(name)


def openai_tools(functions):
    validate_tool_names(functions)
    return convert_to_tool(functions)


def grade_single(pool, message, finish, gold):
    calls = message.get("tool_calls")
    if pool == "irrelevance":
        content = message.get("content")
        return (
            finish == "stop" and (calls is None or calls == [])
            and isinstance(content, str) and bool(content.strip())
        )
    expected = [{normalize_name(name): args for name, args in call.items()} for call in gold]
    return finish != "length" and tool_match(calls, expected)
