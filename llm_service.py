import base64
import io
import json
import os
import time
import urllib.request
import urllib.error
import ssl
from typing import Any, Dict, List, Optional, Union

def get_ssl_context():
    try:
        import certifi
        return ssl.create_default_context(cafile=certifi.where())
    except Exception:
        return ssl._create_unverified_context()


# ============================================================
# .ENV FILE LOADER
# ============================================================

def load_env_file():
    env_path = ".env"
    if os.path.exists(env_path):
        try:
            with open(env_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, value = line.split("=", 1)
                        key = key.strip()
                        value = value.strip().strip("'\"")
                        if key and not os.environ.get(key):
                            os.environ[key] = value
        except Exception:
            pass

load_env_file()

# Supported Providers: 'gemini', 'openai', 'auto'
LLM_PROVIDER = os.environ.get("LLM_PROVIDER", "auto").lower()

DEFAULT_GEMINI_MODEL = os.environ.get("GEMINI_MODEL", os.environ.get("LLM_MODEL", "gemini-3.6-flash"))
DEFAULT_OPENAI_MODEL = os.environ.get("OPENAI_MODEL", os.environ.get("LLM_MODEL", "gpt-4o-mini"))


# ============================================================
# API KEY DISCOVERY & PROVIDER SELECTION
# ============================================================

def detect_active_llm_provider() -> tuple[Optional[str], Optional[str]]:
    """
    Detects which LLM provider API key is set in environment.
    Returns (provider_name, api_key)
    """
    provider_override = os.environ.get("LLM_PROVIDER", "auto").lower()

    if provider_override in ["gemini", "google"]:
        gemini_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        if gemini_key:
            return "gemini", gemini_key

    if provider_override == "openai":
        openai_key = os.environ.get("OPENAI_API_KEY")
        if openai_key:
            return "openai", openai_key

    # Auto-detection priority: Gemini API -> OpenAI API
    gemini_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if gemini_key:
        return "gemini", gemini_key

    openai_key = os.environ.get("OPENAI_API_KEY")
    if openai_key:
        return "openai", openai_key

    return None, None


# ============================================================
# GEMINI LLM GENERATOR (SDK & REST API FALLBACK)
# ============================================================

def generate_gemini_via_rest(
    prompt: str,
    multimodal_context: Optional[Dict[str, Any]] = None,
    api_key: str = "",
    model_name: str = DEFAULT_GEMINI_MODEL
) -> str:
    """REST API generator for Gemini API using standard library urllib with backoff and model fallback."""
    models_to_try = [model_name]
    fallback_models = ["gemini-3.6-flash", "gemini-flash-latest", "gemini-3-flash-preview", "gemini-3.1-pro-preview"]
    for fm in fallback_models:
        if fm not in models_to_try:
            models_to_try.append(fm)

    parts: List[Dict[str, Any]] = [{"text": prompt}]

    if multimodal_context and multimodal_context.get("has_images"):
        for img_detail in multimodal_context.get("image_details", []):
            data_uri = img_detail.get("full_data_uri") or img_detail.get("data_uri", "")
            mime_type = "image/png"
            b64_data = ""

            if "base64," in data_uri:
                header, b64_data = data_uri.split("base64,", 1)
                if "data:" in header and ";base64" in header:
                    mime_type = header.replace("data:", "").replace(";base64", "").strip() or "image/png"
            elif data_uri:
                b64_data = data_uri.strip()

            if b64_data:
                b64_clean = b64_data.strip()
                missing_padding = len(b64_clean) % 4
                if missing_padding:
                    b64_clean += "=" * (4 - missing_padding)

                parts.append({
                    "inline_data": {
                        "mime_type": mime_type,
                        "data": b64_clean
                    }
                })

    payload = {
        "contents": [
            {
                "parts": parts
            }
        ]
    }

    last_error = ""

    for current_model in models_to_try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{current_model}:generateContent?key={api_key}"

        # Up to 2 retries per model for rate limit / temporary 503
        for attempt in range(2):
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={
                    "Content-Type": "application/json",
                    "User-Agent": "PragTutor/1.0"
                },
                method="POST"
            )

            try:
                with urllib.request.urlopen(req, context=get_ssl_context(), timeout=15) as resp:
                    resp_bytes = resp.read()
                    res_json = json.loads(resp_bytes.decode("utf-8"))
                    candidates = res_json.get("candidates", [])
                    if candidates:
                        parts_resp = candidates[0].get("content", {}).get("parts", [])
                        extracted_text = "".join([p.get("text", "") for p in parts_resp if "text" in p])
                        if extracted_text:
                            return extracted_text
                    return "[Gemini API]: Returned empty response."

            except urllib.error.HTTPError as http_err:
                err_body = http_err.read().decode("utf-8", errors="ignore")
                last_error = f"[Gemini LLM Error HTTP {http_err.code}]: {err_body or str(http_err)}"

                # 404 Model Not Found -> try next model immediately
                if http_err.code == 404:
                    break

                # 429 or 503 -> wait and retry once
                if http_err.code in [429, 503] and attempt == 0:
                    time.sleep(2)
                    continue
                else:
                    break

            except Exception as err:
                last_error = f"[Gemini LLM Error]: {err}"
                break

    return last_error or "[Gemini LLM Error]: Failed to get response from Gemini API models."


def generate_gemini_response(
    prompt: str,
    multimodal_context: Optional[Dict[str, Any]] = None,
    api_key: str = ""
) -> str:
    model_name = os.environ.get("GEMINI_MODEL", os.environ.get("LLM_MODEL", DEFAULT_GEMINI_MODEL))

    # 1. Try google-genai (newer SDK)
    try:
        from google import genai
        client = genai.Client(api_key=api_key)
        contents = [prompt]
        if multimodal_context and multimodal_context.get("has_images"):
            for img_detail in multimodal_context.get("image_details", []):
                data_uri = img_detail.get("full_data_uri") or img_detail.get("data_uri", "")
                if data_uri and "base64," in data_uri:
                    b64_data = data_uri.split("base64,")[1].strip()
                    missing_padding = len(b64_data) % 4
                    if missing_padding:
                        b64_data += "=" * (4 - missing_padding)
                    image_bytes = base64.b64decode(b64_data)
                    contents.append(genai.types.Part.from_bytes(data=image_bytes, mime_type="image/png"))

        response = client.models.generate_content(
            model=model_name,
            contents=contents
        )
        return response.text
    except ImportError:
        pass
    except Exception as err:
        pass

    # 2. Try google.generativeai (classic SDK)
    try:
        import google.generativeai as genai
        from PIL import Image

        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(model_name)
        contents = [prompt]

        if multimodal_context and multimodal_context.get("has_images"):
            for img_detail in multimodal_context.get("image_details", []):
                data_uri = img_detail.get("full_data_uri") or img_detail.get("data_uri", "")
                if data_uri and "base64," in data_uri:
                    try:
                        b64_data = data_uri.split("base64,")[1].strip()
                        missing_padding = len(b64_data) % 4
                        if missing_padding:
                            b64_data += "=" * (4 - missing_padding)
                        image_bytes = base64.b64decode(b64_data)
                        pil_img = Image.open(io.BytesIO(image_bytes))
                        contents.append(pil_img)
                    except Exception as img_err:
                        print(f"Warning: Failed to parse image for Gemini SDK: {img_err}")

        response = model.generate_content(contents)
        return response.text
    except ImportError:
        pass
    except Exception as err:
        pass

    # 3. Fallback to urllib direct REST API call
    return generate_gemini_via_rest(
        prompt=prompt,
        multimodal_context=multimodal_context,
        api_key=api_key,
        model_name=model_name
    )


# ============================================================
# OPENAI LLM GENERATOR (SDK & REST API FALLBACK)
# ============================================================

def generate_openai_via_rest(
    prompt: str,
    multimodal_payload: Optional[Union[List[Any], Dict[str, Any]]] = None,
    api_key: str = "",
    model_name: str = DEFAULT_OPENAI_MODEL
) -> str:
    """REST API generator for OpenAI using standard library urllib."""
    url = "https://api.openai.com/v1/chat/completions"

    if multimodal_payload and isinstance(multimodal_payload, list):
        messages = multimodal_payload
    else:
        messages = [{"role": "user", "content": prompt}]

    payload = {
        "model": model_name,
        "messages": messages
    }

    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
            "User-Agent": "PragTutor/1.0"
        },
        method="POST"
    )

    try:
        with urllib.request.urlopen(req, context=get_ssl_context(), timeout=30) as resp:
            resp_bytes = resp.read()
            res_json = json.loads(resp_bytes.decode("utf-8"))
            choices = res_json.get("choices", [])
            if choices:
                return choices[0].get("message", {}).get("content", "")
            return "[OpenAI API]: Returned empty choices."
    except urllib.error.HTTPError as http_err:
        err_body = http_err.read().decode("utf-8", errors="ignore")
        return f"[OpenAI LLM Error HTTP {http_err.code}]: {err_body or str(http_err)}"
    except Exception as err:
        return f"[OpenAI LLM Error]: {err}"


def generate_openai_response(
    prompt: str,
    multimodal_payload: Optional[Union[List[Any], Dict[str, Any]]] = None,
    api_key: str = ""
) -> str:
    model_name = os.environ.get("OPENAI_MODEL", os.environ.get("LLM_MODEL", DEFAULT_OPENAI_MODEL))

    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)

        if multimodal_payload and isinstance(multimodal_payload, list):
            messages = multimodal_payload
        else:
            messages = [{"role": "user", "content": prompt}]

        response = client.chat.completions.create(
            model=model_name,
            messages=messages
        )
        return response.choices[0].message.content
    except ImportError:
        pass
    except Exception as err:
        pass

    # Fallback to urllib direct REST API call
    return generate_openai_via_rest(
        prompt=prompt,
        multimodal_payload=multimodal_payload,
        api_key=api_key,
        model_name=model_name
    )


# ============================================================
# UNIFIED GENERATE RESPONSE
# ============================================================

def generate_response(
    prompt: str,
    multimodal_payload: Optional[Any] = None,
    multimodal_context: Optional[Dict[str, Any]] = None
) -> str:
    """
    Generates tutor response using connected LLM (Google Gemini or OpenAI GPT).
    Auto-detects API key from environment variables.
    """
    provider, api_key = detect_active_llm_provider()

    if not provider or not api_key:
        return (
            "\n" + "=" * 70 + "\n"
            "[PRAGTUTOR LLM CONNECTION NOTICE]\n"
            "=" * 70 + "\n"
            "No active LLM API key detected in your environment or .env file.\n"
            "The backend has successfully generated the dynamic prompt & multimodal context.\n\n"
            "To connect PragTutor to an LLM, provide your API key in the .env file or environment:\n"
            "  - For Gemini API: GEMINI_API_KEY=\"your_gemini_api_key\"\n"
            "  - For OpenAI API: OPENAI_API_KEY=\"your_openai_api_key\"\n"
            "=" * 70
        )

    if provider == "gemini":
        return generate_gemini_response(
            prompt=prompt,
            multimodal_context=multimodal_context,
            api_key=api_key
        )

    elif provider == "openai":
        return generate_openai_response(
            prompt=prompt,
            multimodal_payload=multimodal_payload,
            api_key=api_key
        )

    return "[LLM Error]: Unknown LLM provider specified."


# ============================================================
# TEST FUNCTION
# ============================================================

def test_llm():
    test_prompt = """
You are a helpful Operating Systems tutor.
Explain the concept of a process in simple language.
Give:
1. Definition
2. Simple explanation
3. Example
"""
    provider, api_key = detect_active_llm_provider()
    masked_key = f"{api_key[:6]}...{api_key[-4:]}" if api_key and len(api_key) > 10 else ("Set" if api_key else "None")
    print("=" * 80)
    print("TESTING PRAGTUTOR LLM SERVICE")
    print(f"Active Provider : {provider if provider else 'None (Waiting for API key)'}")
    print(f"API Key Status  : {masked_key}")
    print("=" * 80)

    res = generate_response(test_prompt)
    print(res)


if __name__ == "__main__":
    test_llm()