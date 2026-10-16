#!/usr/bin/env python3
import os, sys
from pathlib import Path
os.execv(sys.executable, [sys.executable, str(Path(__file__).with_name("launch-backend.py")), 'sglang', *sys.argv[1:]])
