"""Pin an intact large text message for repeated document questions in DSH/API."""
import os

MIN_CHARS = 16384


def add_document_prefix(payload):
    """Preserve explicit client policy; never guess a boundary inside a message.

    The native tokenizer validates the exact prefix against the full rendered
    prompt, including tool schemas. No prompt text or session state is retained.
    """
    if 'strata_prefix' in payload or os.environ.get('STRATA_AUTO_PREFIX', '1') != '1':
        return payload
    messages = payload.get('messages')
    if not isinstance(messages, list) or len(messages) < 2:
        return payload
    # Leave multimodal requests to native handling, and require plain text.
    if any(not isinstance(m, dict) or isinstance(m.get('content'), list) for m in messages):
        return payload
    for index, message in enumerate(messages[:-1]):
        content = message.get('content')
        if message.get('role') in ('user', 'tool') and isinstance(content, str) and len(content) >= MIN_CHARS:
            return {**payload, 'strata_prefix': {'messages': index + 1}}
    return payload
