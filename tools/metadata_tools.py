import base64
from pathlib import Path

import requests
from crewai.tools import tool


@tool("analyze_image_via_ollama")
def analyze_image_via_ollama(image_path: str, OLLAMA_HOST: str, OLLAMA_MODEL: str, PHOTO_INFO: str = None) -> str:
    """
    Analyze the image at image_path using Ollama and return a detailed literal description.
    Accepts optional PHOTO_INFO string containing extra metadata for matching files.
    """
    try:
        current_filename = Path(image_path).stem
        additional_context = ""

        if PHOTO_INFO and str(PHOTO_INFO).strip() and (current_filename in PHOTO_INFO):
            extra_info_dict = {}
            pairs = PHOTO_INFO.split(';')
            for pair in pairs:
                if '=' in pair:
                    filename, info = pair.split('=', 1)
                    extra_info_dict[filename.strip()] = info.strip()

            additional_context = extra_info_dict.get(current_filename, "")

        base_prompt = "Describe this image in detail for a microstock presentation. What objects, colors, and potential trademark risks do you see?"
        if additional_context:
            base_prompt += f"\n\nAdditional context or user notes for this specific image: {additional_context}"

        with open(image_path, "rb") as f:
            img_str = base64.b64encode(f.read()).decode("utf-8")

        warmup_payload = {
            "model": OLLAMA_MODEL,
            "prompt": "ping",
            "stream": False,
            "options": {"num_predict": 1},
            "keep_alive": "10m",
        }
        warmup_response = requests.post(f"{OLLAMA_HOST}/api/generate", json=warmup_payload, timeout=60)
        if warmup_response.status_code != 200:
            return f"Error loading model in Ollama: {warmup_response.text}"

        payload = {
            "model": OLLAMA_MODEL,
            "prompt": base_prompt,
            "stream": False,
            "images": [img_str],
        }
        response = requests.post(f"{OLLAMA_HOST}/api/generate", json=payload, timeout=180)

        if response.status_code == 200:
            return response.json().get("response", "No response from model.")
        return f"Error from Ollama: {response.text}"
    except requests.exceptions.RequestException as exc:
        return f"Ollama API request failed: {str(exc)}"
    except Exception as exc:
        return f"Failed to process image: {str(exc)}"
