import json
import os
import re
from pathlib import Path

import httpx

DEFAULT_GEMINI_CONFIG_TIMEOUT_SECONDS = 5.0
DEFAULT_GEMINI_MODEL = "gemini-2.5-flash"


class GeminiConfigError(ValueError):
    pass


class GeminiResponseError(ValueError):
    pass


def configured_api_key() -> str:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise GeminiConfigError("GEMINI_API_KEY is not set")
    return api_key


def gemini_model() -> str:
    return os.getenv("GEMINI_MODEL", DEFAULT_GEMINI_MODEL)


def gemini_url(model: str, api_key: str) -> str:
    return (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"{model}:generateContent?key={api_key}"
    )


def timeout_from_env(name: str, default: float) -> float:
    try:
        value = float(os.getenv(name, str(default)))
    except ValueError:
        return default
    return value if value > 0 else default


async def generate_content(
    payload: dict,
    *,
    api_key: str | None = None,
    model: str | None = None,
    timeout: float,
) -> dict:
    key = api_key or configured_api_key()
    selected_model = model or gemini_model()
    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.post(gemini_url(selected_model, key), json=payload)
        response.raise_for_status()
        return response.json()


async def check_config_status() -> dict:
    model = gemini_model()
    try:
        api_key = configured_api_key()
    except GeminiConfigError as exc:
        return {
            "configured": False,
            "reachable": False,
            "model": model,
            "detail": str(exc),
        }

    payload = {
        "contents": [{"parts": [{"text": "Reply with JSON: {\"ok\": true}"}]}],
        "generationConfig": {"temperature": 0},
    }

    try:
        await generate_content(
            payload,
            api_key=api_key,
            model=model,
            timeout=timeout_from_env(
                "GEMINI_CONFIG_TIMEOUT_SECONDS",
                DEFAULT_GEMINI_CONFIG_TIMEOUT_SECONDS,
            ),
        )
    except httpx.HTTPStatusError as exc:
        return {
            "configured": True,
            "reachable": False,
            "model": model,
            "detail": f"Gemini API returned HTTP {exc.response.status_code}",
        }
    except Exception as exc:
        return {
            "configured": True,
            "reachable": False,
            "model": model,
            "detail": f"Gemini connectivity check failed: {type(exc).__name__}",
        }

    return {
        "configured": True,
        "reachable": True,
        "model": model,
        "detail": "Gemini API reachable",
    }


async def upload_file_to_gemini(
    file_path: Path, mime_type: str, api_key: str | None = None
) -> str:
    key = api_key or configured_api_key()
    num_bytes = file_path.stat().st_size
    start_url = f"https://generativelanguage.googleapis.com/upload/v1beta/files?key={key}"
    metadata = {"file": {"display_name": file_path.name}}
    async with httpx.AsyncClient(timeout=120.0) as client:
        start_response = await client.post(
            start_url,
            headers={
                "X-Goog-Upload-Protocol": "resumable",
                "X-Goog-Upload-Command": "start",
                "X-Goog-Upload-Header-Content-Length": str(num_bytes),
                "X-Goog-Upload-Header-Content-Type": mime_type,
                "Content-Type": "application/json",
            },
            json=metadata,
        )
        start_response.raise_for_status()
        upload_url = start_response.headers.get("X-Goog-Upload-URL")
        if not upload_url:
            raise GeminiResponseError("Gemini File API did not return an upload URL")

        upload_response = await client.post(
            upload_url,
            headers={
                "Content-Length": str(num_bytes),
                "X-Goog-Upload-Offset": "0",
                "X-Goog-Upload-Command": "upload, finalize",
                "Content-Type": mime_type,
            },
            content=file_path.read_bytes(),
        )
        upload_response.raise_for_status()
        data = upload_response.json()

    file_uri = data.get("file", {}).get("uri")
    if not file_uri:
        raise GeminiResponseError("Gemini File API did not return a file URI")
    return file_uri


def extract_model_text(payload: dict) -> str | None:
    candidates = payload.get("candidates", [])
    if not candidates:
        return None

    parts = candidates[0].get("content", {}).get("parts", [])
    if not parts:
        return None

    text_chunks = [part.get("text", "") for part in parts if isinstance(part.get("text"), str)]
    combined = "\n".join(chunk for chunk in text_chunks if chunk.strip())
    return combined if combined else None


def parse_json_response(text: str) -> dict | None:
    try:
        parsed = json.loads(text)
        return parsed if isinstance(parsed, dict) else None
    except json.JSONDecodeError:
        pass

    fenced_blocks = re.findall(r"```(?:json)?\s*([\s\S]*?)\s*```", text, re.IGNORECASE)
    for block in fenced_blocks:
        block = block.strip()
        if not block:
            continue
        try:
            parsed = json.loads(block)
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            # Some responses include extra text alongside JSON.
            pass

        for candidate in extract_json_objects(block):
            try:
                parsed = json.loads(candidate)
                if isinstance(parsed, dict):
                    return parsed
            except json.JSONDecodeError:
                continue

    for candidate in extract_json_objects(text):
        try:
            parsed = json.loads(candidate)
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            continue
    return None


def extract_json_objects(text: str) -> list[str]:
    objects: list[str] = []
    depth = 0
    start = -1
    in_string = False
    escaped = False

    for idx, char in enumerate(text):
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            continue

        if char == '"':
            in_string = True
            continue

        if char == "{":
            if depth == 0:
                start = idx
            depth += 1
        elif char == "}" and depth > 0:
            depth -= 1
            if depth == 0 and start != -1:
                objects.append(text[start : idx + 1])
                start = -1

    return objects
