"""Tiny Google Gemini REST client (free tier works). Shared by the weekly
pipeline and the Script & Copy Studio."""
from __future__ import annotations

import json
import os

import requests

ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
DEFAULT_MODEL = "gemini-2.5-flash"


def call_gemini(prompt: str, api_key: str | None = None, model: str | None = None,
                as_json: bool = True, temperature: float = 0.7, timeout: int = 120):
    key = api_key or os.getenv("GEMINI_API_KEY")
    if not key:
        raise RuntimeError("GEMINI_API_KEY is not set")
    model = model or os.getenv("GEMINI_MODEL") or DEFAULT_MODEL
    cfg = {"temperature": temperature}
    if as_json:
        cfg["responseMimeType"] = "application/json"
    r = requests.post(
        ENDPOINT.format(model=model),
        params={"key": key},
        json={"contents": [{"parts": [{"text": prompt}]}], "generationConfig": cfg},
        timeout=timeout,
    )
    r.raise_for_status()
    text = r.json()["candidates"][0]["content"]["parts"][0]["text"]
    return json.loads(text) if as_json else text
