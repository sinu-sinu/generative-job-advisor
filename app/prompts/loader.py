# app/prompts/loader.py

import os

def load_prompt(filename: str) -> str:
    base_path = os.path.dirname(__file__)
    path = os.path.join(base_path, filename)
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

