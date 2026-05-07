import asyncio
import os
import traceback

import httpx
from dotenv import load_dotenv


async def run():
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    model = os.getenv("GEMINI_MODEL", "gemini-2.5-pro")

    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is not set")

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                url,
                params={"key": api_key},
                json={"contents": [{"parts": [{"text": "hi"}]}]},
            )
            print(response.status_code)
            print(response.text)
    except Exception as exc:
        print(f"Error type: {type(exc).__name__}")
        print(f"Error repr: {exc!r}")
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(run())
