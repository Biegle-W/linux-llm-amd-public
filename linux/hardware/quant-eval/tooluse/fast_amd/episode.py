"""BFCL function-calling episodes."""

from decimal import localcontext
import json
from keyword import iskeyword
import re
from uuid import uuid4

from fast_amd.bfcl import multi_turn_utils
from fast_amd.bfcl.multi_turn_checker import multi_turn_checker
from fast_amd.bfcl.prompts import (
    DEFAULT_USER_PROMPT_FOR_ADDITIONAL_FUNCTION_FC,
    MAXIMUM_STEP_LIMIT,
)
from fast_amd.tooling import normalize_name, openai_tools

# The checker replays decoded strings with eval. Replay rejected calls as a
# fixed undefined name so they count as errors without executing model input.
REJECTED_CALL = "_fast_amd_rejected_tool_call()"


def identifier(value):
    return (
        isinstance(value, str)
        and re.fullmatch(r"[a-zA-Z_]\w*", value, re.ASCII) is not None
        and not iskeyword(value)
    )


def decode_calls(calls, names):
    decoded = []
    errors = []
    for call in calls:
        function = call["function"]
        name = function["name"]
        args = function["arguments"]
        if isinstance(args, str):
            args = json.loads(args)
        if not isinstance(args, dict):
            raise ValueError("Expected an argument object")
        # Reject nonfinite values and keep only literal data before BFCL eval.
        args = json.loads(json.dumps(args, allow_nan=False))
        error = None
        if not identifier(name) or not all(map(identifier, args)):
            error = "Invalid tool name or argument key"
        elif name not in names:
            error = f"name {name!r} is not defined"
        elif not identifier(names[name]):
            error = "Invalid tool name"
        if error is None:
            parameters = ",".join(f"{key}={value!r}" for key, value in args.items())
            decoded.append(f"{names[name]}({parameters})")
            errors.append(None)
        else:
            decoded.append(REJECTED_CALL)
            errors.append(f"Error during execution: {error}")
    return decoded, errors


def evaluate(row, gold, docs, ask):
    namespace = f"episode_{uuid4().hex}"
    try:
        with localcontext():
            return play(row, gold, docs, ask, namespace)
    finally:
        for name in list(vars(multi_turn_utils)):
            if name.startswith(namespace + "_"):
                delattr(multi_turn_utils, name)


def play(row, gold, docs, ask, namespace):
    classes = row["involved_classes"]
    functions = {doc["name"]: doc for name in classes for doc in docs[name]}
    holdouts = row.get("missed_function", {})
    withheld = {name for names in holdouts.values() for name in names}
    visible = [doc for name, doc in functions.items() if name not in withheld]
    tools = openai_tools(visible)
    names = {normalize_name(doc["name"]): doc["name"] for doc in visible}
    messages = []
    decoded_turns = []
    item_id = row["id"]
    category = item_id.rsplit("_", 1)[0]
    initial_config = row["initial_config"]

    def execute(calls):
        results, _ = multi_turn_utils.execute_multi_turn_func_call(
            calls, initial_config, classes, namespace, item_id,
        )
        return results

    execute([])
    force_quit = False
    step = 0
    for turn, user_messages in enumerate(row["question"]):
        if str(turn) in holdouts:
            additions = [functions[name] for name in holdouts[str(turn)]]
            visible.extend(additions)
            tools = openai_tools(visible)
            names.update({normalize_name(doc["name"]): doc["name"] for doc in additions})
            user_messages = [{
                "role": "user", "content": DEFAULT_USER_PROMPT_FOR_ADDITIONAL_FUNCTION_FC,
            }]
        messages.extend(user_messages)
        decoded_steps = []
        count = 0
        while True:
            reply, _ = ask(messages, tools)
            calls = reply.get("tool_calls")
            assistant = {"role": "assistant", "content": reply.get("content") or ""}
            messages.append(assistant)
            if calls is None or calls == []:
                decoded_steps.append([])
                break
            if not isinstance(calls, list):
                assistant["tool_calls"] = calls
                break
            calls = [
                {**call, "id": call.get("id") or f"call_{step}_{index}"}
                if isinstance(call, dict) else call
                for index, call in enumerate(calls)
            ]
            assistant["tool_calls"] = calls
            step += 1
            try:
                decoded, errors = decode_calls(calls, names)
            except (KeyError, TypeError, ValueError, RecursionError):
                break
            decoded_steps.append(decoded)
            results = iter(execute([
                call for call, error in zip(decoded, errors, strict=True) if error is None
            ]))
            for call, error in zip(calls, errors, strict=True):
                messages.append({
                    "role": "tool", "tool_call_id": call["id"],
                    "content": error if error is not None else next(results),
                })
            count += 1
            if count > MAXIMUM_STEP_LIMIT:
                force_quit = True
                break
        decoded_turns.append(decoded_steps)
        if force_quit:
            break

    # BFCL returns the truncated response on a force-quit and fails the
    # entry. Its state checker assumes all ground-truth turns are present.
    if force_quit:
        return False
    return multi_turn_checker(decoded_turns, gold, row, category, namespace)["valid"]
