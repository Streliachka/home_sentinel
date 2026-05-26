
import os
import csv
import json
import re
from pathlib import Path
import time
from dotenv import load_dotenv
import glob
from crewai import Crew, Process, Task, LLM
from agents import visual_analyst, copyright_analyst, legal_auditor, metadata_formatter
from tasks import task_analyze_image,task_gen_description, task_audit_description, task_format_data
from pydantic import BaseModel, Field
from tools import analyze_image_via_ollama

load_dotenv()

OLLAMA_HOST = os.getenv("OLLAMA_BASE_URL")
VISION_MODEL = os.getenv("VISION_MODEL")
PHOTO_INFO = os.getenv("PHOTO_INFO")

class FinalStockMetadata(BaseModel):
    status: str = Field(description="Must be 'CLEANED_AND_APPROVED'")
    modifications_made: str = Field(description="None or description of edits")
    visual_data: str = Field(
        description="Original literal visual description from the visual analyst. This is the unedited, raw description of what is in the image. It should not be changed by the SEO or Legal agents, but it should be included in the final output for reference."
    )
    title: str = Field(
        description="A natural, descriptive English sentence (7-15 words). NO '+' signs, NO slashes."
    )
    keywords: list[str] = Field(
        description="List of 35-45 STRICTLY SINGLE WORDS or 2-word phrases max separated by ';'. All lowercase. Absolutely NO long sentences, NO phrases with 'and'. Example: ['cyberpunk'; 'leather corset'; 'prague'; 'winter'; 'sunset']."
    )


# Agents
visual_analyst_agent = visual_analyst
visual_analyst_agent.tools = [analyze_image_via_ollama]

copyright_analyst_agent = copyright_analyst

legal_auditor_agent = legal_auditor
metadata_formatter_agent = metadata_formatter

# Tasks
taskAnalyzeImage = task_analyze_image
taskAnalyzeImage.agent = visual_analyst_agent

taskGenDescription = task_gen_description
taskGenDescription.agent = copyright_analyst_agent
taskGenDescription.context = [taskAnalyzeImage]
taskGenDescription.output_json = FinalStockMetadata

taskAuditDescription = task_audit_description
taskAuditDescription.agent = legal_auditor_agent
taskAuditDescription.context = [taskAnalyzeImage, taskGenDescription]
taskAuditDescription.output_json = FinalStockMetadata

taskMetadataFinalFormat = task_format_data
taskMetadataFinalFormat.agent = metadata_formatter_agent
taskMetadataFinalFormat.context = [taskAnalyzeImage, taskGenDescription]
taskMetadataFinalFormat.output_json = FinalStockMetadata


shutter_crew = Crew(
    agents=[visual_analyst_agent, copyright_analyst_agent],
    tasks=[taskAnalyzeImage, taskGenDescription],
    process=Process.sequential,
    verbose=True
    )

shutter_crew_gemini = Crew(
    agents=[visual_analyst_agent, copyright_analyst_agent, metadata_formatter_agent],
    tasks=[taskAnalyzeImage, taskGenDescription, taskMetadataFinalFormat],
    process=Process.sequential,
    verbose=True
    )

def parse_crew_result(result) -> dict:
    """
    Вспомогательная функция для извлечения данных из CrewAI.
    Возвращает словарь с чистыми строками.
    """
    # 1. Если вернулся Pydantic объект
    if hasattr(result, 'pydantic') and result.pydantic:
        data = result.pydantic
        kw = getattr(data, 'keywords', [])
        return {
            "description": getattr(data, 'visual_data', ''),
            "title": getattr(data, 'title', 'Untitled Stock Photo'),
            "keywords": ";".join(kw) if isinstance(kw, list) else str(kw),
            "status": getattr(data, 'status', 'APPROVED'),
            "modifications": getattr(data, 'modifications_made', '')
        }
    
    # 2. Если вернулся raw JSON/текст
    raw_text = result.raw if hasattr(result, 'raw') else str(result)
    json_match = re.search(r'\{.*\}', raw_text, re.DOTALL)
    
    if json_match:
        data_dict = json.loads(json_match.group(0))
        kw = data_dict.get('keywords', [])
        return {
            "description": data_dict.get('visual_data', ''),
            "title": data_dict.get('title', 'Untitled Stock Photo'),
            "keywords": ";".join(kw) if isinstance(kw, list) else str(kw),
            "status": data_dict.get('status', 'CLEANED_AND_APPROVED'),
            "modifications": data_dict.get('modifications_made', 'Parsed from JSON string')
        }
        
    raise ValueError("Could not find a JSON structure in the model response")


def process_stock_folder(folder_path, output_csv_path="shutterstock_batch.csv"):
    """
    Scans a folder, runs each photo through the CrewAI pipeline,
    and writes results parallel to CSV and formatted TXT files.
    """
    folder = Path(folder_path)
    # Современный поиск файлов: ищет jpeg/jpg в любом регистре без дубликатов
    extensions = {'.jpg', '.jpeg'}
    image_files = [f for f in folder.iterdir() if f.is_file() and f.suffix.lower() in extensions]

    if not image_files:
        print(f"No images in {folder_path}.")
        return

    print(f"Images to process: {len(image_files)}")
    
    # Формируем путь для TXT (с тем же именем, что и CSV)
    output_txt_path = Path(output_csv_path).with_suffix('.txt')
    
    csv_headers = ["Filename", "Description", "Title", "Keywords", "Status", "Modifications"]
    csv_exists = Path(output_csv_path).is_file()
    
    # Открываем оба файла параллельно
    with open(output_csv_path, mode='a', newline='', encoding='utf-8') as csv_file, \
         open(output_txt_path, mode='a', encoding='utf-8') as txt_file:
        
        writer = csv.writer(csv_file, delimiter=',')
        if not csv_exists:
            writer.writerow(csv_headers)
            
        for index, img_path in enumerate(image_files, start=1):
            filename = img_path.name
            print(f"\n[{index}/{len(image_files)}] Processing: {filename}...")
            
            test_inputs = {
                "image_path": str(img_path),
                "OLLAMA_HOST": OLLAMA_HOST,
                "OLLAMA_MODEL": VISION_MODEL,
                "PHOTO_INFO": PHOTO_INFO
            }
            
            try:
                # Запуск пайплайна
                result = shutter_crew_gemini.kickoff(inputs=test_inputs)
                
                # Парсинг данных через внешнюю функцию
                res_data = parse_crew_result(result)
                
                # Добавляем префиксы для сохранения
                final_title = f"TitleData: {res_data['title']}"
                final_keywords = f"KeywordsData: {res_data['keywords']}"
                
                # 1. Запись в CSV
                writer.writerow([
                    filename, 
                    res_data['description'], 
                    final_title, 
                    final_keywords, 
                    res_data['status'], 
                    res_data['modifications']
                ])
                csv_file.flush()

                # 2. Запись в TXT (каждое поле с новой строки + пустая строка в конце)
                txt_file.write(
                    f"Filename: {filename}\n"
                    f"Description: {res_data['description']}\n"
                    f"Title: {final_title}\n"
                    f"Keywords: {final_keywords}\n"
                    f"Status: {res_data['status']}\n"
                    f"Modifications: {res_data['modifications']}\n"
                    f"\n" # Пропуск строки между фотографиями
                )
                txt_file.flush()

                # Вывод в консоль
                print(f"\n--- [ДАННЫЕ ФАЙЛА УСПЕШНО ЗАПИСАНЫ] ---")
                print(f"Filename: {filename}")
                print(f"Description: {res_data['description']}")
                print(f"{final_title}")
                print(f"{final_keywords}")
                print(f"Status: {res_data['status']}")
                print(f"Modifications: {res_data['modifications']}")
                print(f"----------------------------------------\n")
                
                time.sleep(4)

            except Exception as e:
                error_msg = str(e)
                print(f"Failed to parse {filename}: {error_msg}")
                
                # Пишем ошибку в CSV
                writer.writerow([filename, "ERROR: Parsing Failed", "", "", "FAILED", error_msg])
                csv_file.flush()
                
                # Пишем ошибку в TXT, сохраняя структуру
                txt_file.write(
                    f"Filename: {filename}\n"
                    f"Description: ERROR: Parsing Failed\n"
                    f"Title: \n"
                    f"Keywords: \n"
                    f"Status: FAILED\n"
                    f"Modifications: {error_msg}\n"
                    f"\n"
                )
                txt_file.flush()
                continue

  
    
# if __name__ == "__main__":
#     image_path = r"C:\Users\oprokopenko\Dropbox\Actum\Photo\SocialNetworksImages\windmill-4.jpg"
#     test_inputs = {
#             "image_path": image_path,
#             "OLLAMA_HOST": OLLAMA_HOST,
#             "OLLAMA_MODEL": VISION_MODEL,
#         }

#     print("Starting local Microstock CrewAI Factory...")
#     result = shutter_crew.kickoff(inputs=test_inputs)

#     print("\nFINAL LEGALLY SAFE METADATA RESULT:")
#     print(result)

if __name__ == "__main__":
    TARGET_FOLDER = r"D:\Photo\Edited\ByDate\2026_Edited\Preview"
    OUTPUT_FILE = "./shutterstock_upload.csv"
    
    process_stock_folder(TARGET_FOLDER, OUTPUT_FILE)