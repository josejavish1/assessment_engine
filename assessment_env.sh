#!/bin/bash
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
    .venv/bin/pip install -e .
fi
source .venv/bin/activate
