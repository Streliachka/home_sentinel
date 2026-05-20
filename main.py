
import os
import csv
from pathlib import Path
from dotenv import load_dotenv
import glob
from crewai import Crew, Process, Task, LLM
from agents import visual_analyst, seo_strategist, legal_auditor, metadata_formatter
from tasks import task_analyze_image,task_gen_description, task_audit_description, task_format_data
from pydantic import BaseModel, Field
from tools import analyze_image_via_ollama

# Set environment variables
os.environ["CREWAI_TELEMETRY_OPT_OUT"] = "true"
os.environ["OPENAI_API_KEY"] = "sk-ollama-local"
load_dotenv()
OLLAMA_HOST = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
os.environ["OLLAMA_BASE_URL"] = OLLAMA_HOST

LOCAL_MODEL = "ollama/llama3.2:3b"
#LOCAL_MODEL = "ollama/llama3.1:8b"
#VISION_MODEL = "llava:7b"
VISION_MODEL = "moondream:latest"
#VISION_MODEL = "gemma4:latest"

if not os.getenv("GEMINI_API_KEY"):
    raise ValueError("no gemini API key found.")

class FinalStockMetadata(BaseModel):
    status: str = Field(description="Must be 'CLEANED_AND_APPROVED'")
    modifications_made: str = Field(description="None or description of edits")
    title: str = Field(
        description="A natural, descriptive English sentence (7-15 words). NO '+' signs, NO slashes."
    )
    keywords: list[str] = Field(
        description="List of 35-45 STRICTLY SINGLE WORDS or 2-word phrases max separated by ';'. All lowercase. Absolutely NO long sentences, NO phrases with 'and'. Example: ['cyberpunk'; 'leather corset'; 'prague'; 'winter'; 'sunset']."
    )

LOCAL_MODEL_OBJ = LLM(
    model=LOCAL_MODEL, 
    base_url=OLLAMA_HOST,
    temperature=0.2
)

VISION_MODEL_OBJ = LLM(
    model=VISION_MODEL, 
    base_url=OLLAMA_HOST
)

GEMINI = LLM(
    model="google/gemini-3.5-flash",
    temperature=0.0,
    api_key=os.getenv("GEMINI_API_KEY")
)

# Agents
visual_analyst_agent = visual_analyst
visual_analyst_agent.llm = LOCAL_MODEL_OBJ
visual_analyst_agent.tools = [analyze_image_via_ollama]

seo_strategist_agent = seo_strategist
seo_strategist_agent.llm = LOCAL_MODEL_OBJ

legal_auditor_agent = legal_auditor
legal_auditor_agent.llm = LOCAL_MODEL_OBJ

metadata_formatter_agent = metadata_formatter
metadata_formatter_agent.llm = GEMINI

# Tasks
taskAnalyzeImage = task_analyze_image
taskAnalyzeImage.agent = visual_analyst_agent

taskGenDescription = task_gen_description
taskGenDescription.agent = seo_strategist_agent
taskGenDescription.context = [taskAnalyzeImage]

taskAuditDescription = task_audit_description
taskAuditDescription.agent = legal_auditor_agent
taskAuditDescription.context = [taskGenDescription]
taskAuditDescription.output_json = FinalStockMetadata

metadataFinalFormat = task_format_data
metadataFinalFormat.agent = metadata_formatter_agent
metadataFinalFormat.context = [taskAnalyzeImage, taskAuditDescription]
metadataFinalFormat.output_json = FinalStockMetadata


shutter_crew = Crew(
    agents=[visual_analyst_agent, seo_strategist_agent, legal_auditor_agent, metadata_formatter_agent],
    tasks=[taskAnalyzeImage, taskGenDescription, taskAuditDescription, metadataFinalFormat],
    process=Process.sequential,
    verbose=True
    )

def process_stock_folder(folder_path, output_csv_path="shutterstock_batch.csv"):
    """
    Scans a folder, runs each photo through the CrewAI pipeline,
    and writes the results to a single CSV file.
    """
    # Supported formats (Shutterstock accepts JPG/JPEG)
    extensions = ('*.jpg', '*.jpeg', '*.JPG', '*.JPEG')
    image_files = []
    for ext in extensions:
        image_files.extend(glob.glob(os.path.join(folder_path, ext)))
        
    if not image_files:
        print(f"No images in {folder_path}.")
        return

    print(f"Images to process: {len(image_files)}")
    
    # CSV headers that Shutterstock expects
    # Filename | Title | Keywords
    csv_headers = ["Filename", "Title", "Keywords", "Status", "Modifications"]
    
    # Check whether the file exists so we don't overwrite previous data
    file_exists = os.path.isfile(output_csv_path)
    
    with open(output_csv_path, mode='a', newline='', encoding='utf-8') as csv_file:
        writer = csv.writer(csv_file, delimiter=',')
        if not file_exists:
            writer.writerow(csv_headers) # Write the header only once
            
        for index, img_path in enumerate(image_files, start=1):
            filename = os.path.basename(img_path)
            print(f"\n[{index}/{len(image_files)}] Processing: {filename}...")
            
            test_inputs = {
                "image_path": img_path,
                "OLLAMA_HOST": OLLAMA_HOST,
                "OLLAMA_MODEL": VISION_MODEL
            }
            
            try:
                # 1. Run the agent pipeline
                result = shutter_crew.kickoff(inputs=test_inputs)
                
                title = ""
                keywords_str = ""
                status = "CLEANED_AND_APPROVED"
                modifications = "Processed successfully"

                # 2. CHECK OPTION A: CrewAI returned a valid Pydantic object
                if hasattr(result, 'pydantic') and result.pydantic:
                    data = result.pydantic
                    title = data.title
                    keywords_str = ", ".join(data.keywords)
                    status = getattr(data, 'status', 'APPROVED')
                    modifications = getattr(data, 'modifications_made', '')
                
                # 3. CHECK OPTION B: Gemini returned raw JSON text in a string
                else:
                    import json
                    import re
                    
                    # Extract response text (in CrewAI this is usually result.raw or str(result))
                    raw_text = result.raw if hasattr(result, 'raw') else str(result)
                    json_match = re.search(r'\{.*\}', raw_text, re.DOTALL)
                    if json_match:
                        clean_json_str = json_match.group(0)
                        data_dict = json.loads(clean_json_str)
                        
                        title = data_dict.get('title', 'Untitled Stock Photo')
                        kw_data = data_dict.get('keywords', [])
                        if isinstance(kw_data, list):
                            keywords_str = ";".join(kw_data)
                        else:
                            keywords_str = str(kw_data)
                            
                        status = data_dict.get('status', 'CLEANED_AND_APPROVED')
                        modifications = data_dict.get('modifications_made', 'Parsed from JSON string')
                    else:
                        raise ValueError("Could not find a JSON structure in the model response")

                    # Write clean, filtered data to CSV
                    writer.writerow([filename, title, keywords_str, status, modifications])
                    csv_file.flush() # Save immediately to avoid data loss
                    print(f"Successfully written to CSV: {filename}")
                    print(f"   Title: {title[:50]}...")
                
            except Exception as e:
                print(f"Failed to parse {filename}: {str(e)}")
                writer.writerow([filename, "ERROR: Parsing Failed", "", "FAILED", str(e)])
                continue

    print(f"\nBatch processing completed! Results saved to: {output_csv_path}")
    
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
    TARGET_FOLDER = r"C:\Users\oprokopenko\Dropbox\Actum\Photo\SocialNetworksImages"
    OUTPUT_FILE = "./shutterstock_upload.csv"
    
    process_stock_folder(TARGET_FOLDER, OUTPUT_FILE)