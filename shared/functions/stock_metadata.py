import csv
import json
import re
import time
from pathlib import Path


def parse_crew_result(result) -> dict:
    """Normalize a CrewAI result into a consistent metadata dictionary."""
    if hasattr(result, "pydantic") and result.pydantic:
        data = result.pydantic
        keywords = getattr(data, "keywords", [])
        return {
            "description": getattr(data, "visual_data", ""),
            "title": getattr(data, "title", "Untitled Stock Photo"),
            "keywords": ";".join(keywords) if isinstance(keywords, list) else str(keywords),
            "status": getattr(data, "status", "APPROVED"),
            "modifications": getattr(data, "modifications_made", ""),
        }

    raw_text = result.raw if hasattr(result, "raw") else str(result)
    json_match = re.search(r"\{.*\}", raw_text, re.DOTALL)
    if not json_match:
        raise ValueError("Could not find a JSON structure in the model response")

    data_dict = json.loads(json_match.group(0))
    keywords = data_dict.get("keywords", [])
    return {
        "description": data_dict.get("visual_data", ""),
        "title": data_dict.get("title", "Untitled Stock Photo"),
        "keywords": ";".join(keywords) if isinstance(keywords, list) else str(keywords),
        "status": data_dict.get("status", "CLEANED_AND_APPROVED"),
        "modifications": data_dict.get("modifications_made", "Parsed from JSON string"),
    }


def process_stock_folder(
    folder_path: str,
    output_csv_path: str,
    selected_crew,
    ollama_host: str,
    ollama_model: str,
    photo_info: str | None,
    delay_sec: float,
) -> None:
    """Run one CrewAI batch invocation for a folder and persist per-image CSV/TXT outputs."""
    folder = Path(folder_path)
    extensions = {".jpg", ".jpeg", ".png"}

    discovered_count = 0
    image_files_map: dict[str, Path] = {}
    for file_path in folder.iterdir():
        if not file_path.is_file() or file_path.suffix.lower() not in extensions:
            continue

        discovered_count += 1

        # De-duplicate case-variant paths (e.g. .JPG vs .jpg) and keep first seen.
        dedupe_key = str(file_path.resolve()).lower()
        image_files_map.setdefault(dedupe_key, file_path)

    image_files = list(image_files_map.values())

    if not image_files:
        print(f"No images in {folder_path}.")
        return

    print(f"Discovered files: {discovered_count}; unique after dedupe: {len(image_files)}")
    print(f"Images to process: {len(image_files)}")
    output_txt_path = Path(output_csv_path).with_suffix(".txt")
    csv_headers = ["Filename", "Description", "Title", "Keywords", "Status", "Modifications"]
    csv_exists = Path(output_csv_path).is_file()

    with open(output_csv_path, mode="a", newline="", encoding="utf-8") as csv_file, open(
        output_txt_path, mode="a", encoding="utf-8"
    ) as txt_file:
        writer = csv.writer(csv_file, delimiter=",")
        if not csv_exists:
            writer.writerow(csv_headers)

        for index, img_path in enumerate(image_files, start=1):
            filename = img_path.name
            print(f"\n[{index}/{len(image_files)}] Processing: {filename}...")

            test_inputs = {
                "image_path": str(img_path),
                "OLLAMA_HOST": ollama_host,
                "OLLAMA_MODEL": ollama_model,
                "PHOTO_INFO": photo_info,
            }

            try:
                result = selected_crew.kickoff(inputs=test_inputs)
                res_data = parse_crew_result(result)

                final_title = f"TitleData: {res_data['title']}"
                final_keywords = f"KeywordsData: {res_data['keywords']}"

                writer.writerow(
                    [
                        filename,
                        res_data["description"],
                        final_title,
                        final_keywords,
                        res_data["status"],
                        res_data["modifications"],
                    ]
                )
                csv_file.flush()

                txt_file.write(
                    f"Filename: {filename}\n"
                    f"Description: {res_data['description']}\n"
                    f"Title: {final_title}\n"
                    f"Keywords: {final_keywords}\n"
                    f"Status: {res_data['status']}\n"
                    f"Modifications: {res_data['modifications']}\n\n"
                )
                txt_file.flush()

                # Keep optional delay between result writes for compatibility with existing CLI arg.
                if delay_sec > 0:
                    time.sleep(delay_sec)
            except Exception as exc:
                error_msg = str(exc)
                print(f"Failed to parse {filename}: {error_msg}")
                writer.writerow([filename, "ERROR: Parsing Failed", "", "", "FAILED", error_msg])
                csv_file.flush()
                txt_file.write(
                    f"Filename: {filename}\n"
                    f"Description: ERROR: Parsing Failed\n"
                    f"Title: \n"
                    f"Keywords: \n"
                    f"Status: FAILED\n"
                    f"Modifications: {error_msg}\n\n"
                )
                txt_file.flush()