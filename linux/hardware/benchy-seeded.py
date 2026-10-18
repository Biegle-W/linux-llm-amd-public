#!/usr/bin/env python3
"""Run llama-benchy with repeatable book offsets and cache-avoidance UUIDs."""
import random
import types
import uuid
import numpy as np
import llama_benchy.prompts as prompts
from llama_benchy.__main__ import main

# Change only benchmark text selection/noise; do not replace UUIDs globally.
np.random.seed(42)
noise = random.Random(42)
prompts.uuid = types.SimpleNamespace(uuid4=lambda: uuid.UUID(int=noise.getrandbits(128),version=4))
main()
