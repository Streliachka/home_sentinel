import os
import json
import glob
import ast
from pathlib import Path
from PIL import Image
from PIL.ExifTags import TAGS

from crewai.tools import tool


def _build_style_llm_client():
    """Create an OpenAI-compatible client for Ollama or Gemini based on environment configuration."""
    import openai

    provider = (os.getenv("STYLE_LLM_PROVIDER") or "ollama").strip().lower()
    style_model = (os.getenv("STYLE_LLM_MODEL") or "").strip()
    ollama_host = (os.getenv("OLLAMA_BASE_URL") or "").strip().rstrip("/")
    local_model = (os.getenv("LOCAL_MODEL") or "").strip()
    vision_model = (os.getenv("VISION_MODEL") or "").strip()
    gemini_model = (os.getenv("GEMINI_MODEL") or "").strip()
    gemini_api_key = (os.getenv("GEMINI_API_KEY") or "").strip()

    if provider == "gemini":
        model_name = style_model or gemini_model
        if not model_name:
            raise ValueError("STYLE_LLM_MODEL or GEMINI_MODEL is required when STYLE_LLM_PROVIDER=gemini")
        if not gemini_api_key:
            raise ValueError("GEMINI_API_KEY is required when STYLE_LLM_PROVIDER=gemini")
        client = openai.OpenAI(
            api_key=gemini_api_key,
            base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
        )
        return client, model_name, provider

    # Default provider: Ollama
    model_name = vision_model or style_model or local_model
    if not model_name:
        raise ValueError(
            "VISION_MODEL or STYLE_LLM_MODEL or LOCAL_MODEL is required when STYLE_LLM_PROVIDER=ollama"
        )

    # Accept values like "ollama/llama3.2:3b" in env vars and normalize for Ollama API.
    if model_name.startswith("ollama/"):
        model_name = model_name.split("/", 1)[1].strip()

    if not ollama_host:
        raise ValueError("OLLAMA_BASE_URL is required when STYLE_LLM_PROVIDER=ollama")

    client = openai.OpenAI(
        base_url=f"{ollama_host}/v1",
        api_key=os.getenv("OLLAMA_API_KEY", "ollama"),
    )
    return client, model_name, provider


def _resolve_style_data_dir(style_data_dir: str) -> Path:
    path = Path(style_data_dir)
    if not path.is_absolute():
        path = Path.cwd() / path
    path.mkdir(parents=True, exist_ok=True)
    return path


def _normalize_tool_value(raw_value: str | None) -> str:
    """Normalize tool-call wrapper payloads like {'value': '...'} or [{'value': '...'}]."""
    if raw_value is None:
        return ""

    value = str(raw_value).strip()
    if not value:
        return ""

    if value.startswith("{") and value.endswith("}"):
        try:
            maybe_dict = ast.literal_eval(value)
            if isinstance(maybe_dict, dict) and "value" in maybe_dict:
                return str(maybe_dict["value"]).strip()
        except Exception:
            return value

    if value.startswith("[") and value.endswith("]"):
        try:
            maybe_list = ast.literal_eval(value)
            if isinstance(maybe_list, list) and maybe_list:
                first = maybe_list[0]
                if isinstance(first, dict) and "value" in first:
                    return str(first["value"]).strip()
                if isinstance(first, str):
                    return first.strip()
        except Exception:
            return value

    return value


def _resolve_profile_workspace(candidate_path: str | None) -> Path:
    if not candidate_path or str(candidate_path).strip() in {".", "./"}:
        style_data = Path.cwd() / "styleData"
        if style_data.exists():
            return style_data
        return Path.cwd()

    path = Path(candidate_path)
    if not path.is_absolute():
        path = Path.cwd() / path

    if path.is_dir():
        if any(path.glob("*_profile.json")):
            return path
        style_data = path / "styleData"
        if style_data.is_dir() and any(style_data.glob("*_profile.json")):
            return style_data
    return path


def _looks_like_author_folder(folder: Path) -> bool:
    excluded = {
        ".git",
        ".venv",
        "__pycache__",
        "agents",
        "crew",
        "shared",
        "tasks",
        "tools",
        "styleData",
    }
    if folder.name.startswith(".") or folder.name in excluded:
        return False

    allowed_exts = {".jpg", ".jpeg", ".png"}
    try:
        # Limit scan depth to avoid walking huge trees (for example .venv)
        for item in folder.iterdir():
            if item.is_file() and item.suffix.lower() in allowed_exts:
                return True
            if item.is_dir():
                for nested in item.iterdir():
                    if nested.is_file() and nested.suffix.lower() in allowed_exts:
                        return True
    except Exception:
        return False
    return False

@tool("Structure Scanning Tool")
def scan_root_structure(root_directory: str, style_data_dir: str = "styleData") -> str:
    """Scans author folders under root_directory and writes *_profile.json into styleData workspace."""
    root = Path(root_directory)
    if not root.exists():
        return f"Error: Path {root_directory} does not exist."

    style_data_path = _resolve_style_data_dir(style_data_dir)
    author_folders = [f for f in root.iterdir() if f.is_dir() and _looks_like_author_folder(f)]

    if not author_folders:
        return (
            f"No author folders with supported images were found in {root.resolve()}. "
            f"Workspace is ready at {style_data_path}."
        )

    results = []

    for folder in author_folders:
        author_name = folder.name
        base_data = {
            "author_name": author_name,
            "folder_path": str(folder),
            "analyzed_photos": []
        }

        output_file = style_data_path / f"{author_name}_profile.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(base_data, f, indent=4, ensure_ascii=False)

        results.append(f"Basic profile created for {author_name} at {output_file}")

    return "\n".join(results)


@tool("Read Profile Files Tool")
def read_profile_files(style_data_dir: str = "styleData") -> str:
    """Reads all *_profile.json files from styleData workspace and returns combined JSON content for analysis."""
    normalized_dir = _normalize_tool_value(style_data_dir)
    root = _resolve_profile_workspace(normalized_dir)
    profile_files = sorted(root.glob("*_profile.json"))
    if not profile_files:
        return f"No *_profile.json files found in {root.resolve()}."

    payload = []
    for file_path in profile_files:
        try:
            payload.append(
                {
                    "file": str(file_path),
                    "data": json.loads(file_path.read_text(encoding="utf-8")),
                }
            )
        except Exception as exc:
            payload.append({"file": str(file_path), "error": str(exc)})

    return json.dumps(payload, ensure_ascii=False)


@tool("Deep Photo Analyzer Tool")
def analyze_photos_in_folder(author_json_path: str = "", object: str = "") -> str:
    """Analyzes one or many *_profile.json files and enriches each profile with photo analysis data."""

    def _analyze_single_profile(profile_path: Path, client, model_name: str, provider_name: str) -> dict:
        def _build_author_style_profile(analyzed_photos: list[dict]) -> dict:
            valid_items = [item for item in analyzed_photos if isinstance(item, dict) and not item.get("error")]
            if not valid_items:
                return {
                    "status": "unavailable",
                    "reason": "No successful photo analyses available for synthesis.",
                }

            prompt = f"""
            You are given structured photo-analysis notes for a single author.
            Build a concise but detailed author-level style synthesis as JSON.

            Source analysis:
            {json.dumps(valid_items, ensure_ascii=False)}

            Return strict JSON with keys:
            - style_identity
            - philosophy
            - intentions
            - emotional_tone
            - composition_strategy
            - light_and_shadow_logic
            - color_intent
            - post_processing_signature
            - viewer_impact
            - confidence

            Rules:
            - Keep each field as a short paragraph (2-4 sentences).
            - Base claims only on provided analysis.
            - If uncertain, state assumptions explicitly inside the field text.
            - confidence must be one of: low, medium, high.
            """

            try:
                response = client.chat.completions.create(
                    model=model_name,
                    response_format={"type": "json_object"},
                    messages=[
                        {
                            "role": "system",
                            "content": "You synthesize author style philosophy and artistic intent from technical and visual evidence.",
                        },
                        {"role": "user", "content": prompt},
                    ],
                )
                profile = json.loads(response.choices[0].message.content)
                profile["photos_used"] = len(valid_items)
                return profile
            except Exception as exc:
                return {
                    "status": "unavailable",
                    "reason": f"Author style synthesis failed: {str(exc)}",
                    "photos_used": len(valid_items),
                }

        with open(profile_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        folder_path = Path(data.get("folder_path", ""))
        extensions = ('*.jpg', '*.jpeg', '*.png')
        photo_files = []
        for ext in extensions:
            photo_files.extend(glob.glob(str(folder_path / ext)))

        if not photo_files:
            return {
                "profile": str(profile_path),
                "status": f"No supported images found in folder {folder_path}.",
            }

        analyzed_list = []
        for photo_path in photo_files[:5]:
            p = Path(photo_path)

            exif_data = {}
            try:
                with Image.open(p) as img:
                    info = img._getexif()
                    if info:
                        for tag, value in info.items():
                            decoded = TAGS.get(tag, tag)
                            if decoded in ['Make', 'Model', 'ExposureTime', 'FNumber', 'ISOSpeedRatings', 'FocalLength']:
                                exif_data[decoded] = str(value)
            except Exception as exc:
                exif_data = {"error": f"Failed to read EXIF: {str(exc)}"}

            prompt = f"""
            Analyze the artistic features of the photo '{p.name}'.
            Technical EXIF data: {json.dumps(exif_data)}

            Provide detailed evaluation based on the following criteria:
            1. Work with black and shadows (crushed to deep black or lifted to matte haze).
            2. Tonal and color minimalism (degree of desaturation of parasitic colors, dominant HEX tones, presence of selective accent color).
            3. Fine art composition markers (presence of geometry, leading lines, percentage of frame filled with negative space, scale of silhouette/subject).
            4. Texture and sharpness usage (microcontrast curve, presence of film grain or razor sharpness on contours).
            5. Extract dominant colors as a list with hex codes and estimated percentage share of frame.
            6. Classify the most likely color harmony using Itten color-wheel logic.

            Return the response strictly in short JSON format with keys:
            - "filename"
            - "exif"
            - "shadow_analysis"
            - "color_analysis"
            - "composition_analysis"
            - "texture_analysis"
            - "dominant_colors" (array of objects: {{"name": "...", "hex": "#RRGGBB", "approx_share_percent": number}})
            - "itten_color_scheme" (object with: {{"scheme": "monochromatic|analogous|complementary|split_complementary|triadic|tetradic|warm_cool_contrast|light_dark_contrast|saturation_contrast|extension_contrast", "confidence": "low|medium|high", "justification": "..."}})

            Rules:
            - Use valid 6-digit HEX values.
            - dominant_colors should contain 3 to 7 items ordered by prevalence.
            - approx_share_percent values should approximately sum to 100.
            """

            try:
                response = client.chat.completions.create(
                    model=model_name,
                    response_format={"type": "json_object"},
                    messages=[
                        {"role": "system", "content": "You are a professional art director and expert in technical analysis of Fine Art photography."},
                        {"role": "user", "content": prompt},
                    ],
                )
                photo_analysis = json.loads(response.choices[0].message.content)
                photo_analysis["analysis_provider"] = provider_name
                photo_analysis["analysis_model"] = model_name
                analyzed_list.append(photo_analysis)
            except Exception as exc:
                analyzed_list.append({"filename": p.name, "error": str(exc)})

        data["analyzed_photos"] = analyzed_list
        data["author_style_profile"] = _build_author_style_profile(analyzed_list)
        with open(profile_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

        return {
            "profile": str(profile_path),
            "status": f"Deep photo analysis completed for {data.get('author_name', profile_path.stem)}.",
            "photos_processed": len(analyzed_list),
        }

    try:
        client, model_name, provider_name = _build_style_llm_client()
    except Exception as exc:
        return f"Style analyzer configuration error: {str(exc)}"

    if not author_json_path and object:
        parsed_object = _normalize_tool_value(object)
        if parsed_object.startswith("{") and parsed_object.endswith("}"):
            try:
                object_dict = ast.literal_eval(parsed_object)
                if isinstance(object_dict, dict) and "author_json_path" in object_dict:
                    author_json_path = str(object_dict["author_json_path"])
            except Exception:
                author_json_path = parsed_object
        else:
            author_json_path = parsed_object

    normalized_path = _normalize_tool_value(author_json_path)
    path_obj = _resolve_profile_workspace(normalized_path)

    if path_obj and path_obj.is_file() and path_obj.suffix.lower() == ".json":
        result = _analyze_single_profile(path_obj, client, model_name, provider_name)
        return json.dumps(result, ensure_ascii=False)

    project_root = path_obj if path_obj and path_obj.is_dir() else _resolve_profile_workspace("styleData")
    profile_files = sorted(project_root.glob("*_profile.json"))
    if not profile_files:
        return f"No *_profile.json files found in {project_root.resolve()}."

    summary = [
        _analyze_single_profile(profile_path, client, model_name, provider_name)
        for profile_path in profile_files
    ]
    return json.dumps(summary, ensure_ascii=False)