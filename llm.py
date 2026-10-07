"""MEMBER 3 owns this file.
ONE function the whole project uses to talk to an AI model:  call_llm(prompt, system) -> text
Choose the provider in your .env file (LLM_PROVIDER=gemini | groq | anthropic | mock).
"""
import os

from dotenv import load_dotenv

load_dotenv()


def call_llm(prompt: str, system: str = "") -> str:
    provider = os.getenv("LLM_PROVIDER", "gemini").lower()
    model = os.getenv("LLM_MODEL", "")

    if provider == "mock":  # no API key needed; only answers a few demo questions
        from src.mock_llm import mock_llm
        return mock_llm(prompt)

    if provider == "gemini":
        from google import genai
        from google.genai import types
        client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
        resp = client.models.generate_content(
            model=model or "gemini-3.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(system_instruction=system or None, temperature=0),
        )
        return resp.text

    if provider == "groq":
        from groq import Groq
        client = Groq(api_key=os.environ["GROQ_API_KEY"])
        resp = client.chat.completions.create(
            model=model or "llama-3.3-70b-versatile",
            temperature=0,
            messages=[{"role": "system", "content": system or "You are a helpful assistant."},
                      {"role": "user", "content": prompt}],
        )
        return resp.choices[0].message.content

    if provider == "anthropic":
        import anthropic
        client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
        resp = client.messages.create(
            model=model or "claude-haiku-4-5-20251001",
            max_tokens=2000,
            temperature=0,
            system=system or "You are a helpful assistant.",
            messages=[{"role": "user", "content": prompt}],
        )
        return resp.content[0].text

    raise ValueError(f"Unknown LLM_PROVIDER: {provider}")
