from crewai import Crew, Process
from agents.metadata_agents import visual_analyst, copyright_analyst, legal_auditor, metadata_formatter
from tasks.metadata_tasks import task_analyze_image,task_gen_description, task_audit_description, task_format_data
from tools.metadata_tools import analyze_image_via_ollama
from shared.classes.final_stock_metadata import FinalStockMetadata

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
if metadata_formatter_agent is not None:
    taskMetadataFinalFormat.agent = metadata_formatter_agent
    taskMetadataFinalFormat.context = [taskAnalyzeImage, taskGenDescription]
    taskMetadataFinalFormat.output_json = FinalStockMetadata


shutter_crew = Crew(
    agents=[visual_analyst_agent, copyright_analyst_agent],
    tasks=[taskAnalyzeImage, taskGenDescription],
    process=Process.sequential,
    verbose=True
    )

shutter_crew_gemini = None
if metadata_formatter_agent is not None:
    shutter_crew_gemini = Crew(
        agents=[visual_analyst_agent, copyright_analyst_agent, metadata_formatter_agent],
        tasks=[taskAnalyzeImage, taskGenDescription, taskMetadataFinalFormat],
        process=Process.sequential,
        verbose=True
        )
    
    #In main.py, after defining the crews and tasks, you can call the crew on a folder of images to process them and generate metadata. For example:
    # TARGET_FOLDER = r"C:\Users\oprokopenko\Dropbox\Actum\Photo\SocialNetworksImages\preview"
    # OUTPUT_FILE = "./shutterstock_upload.csv"
    
    # process_stock_folder(TARGET_FOLDER, OUTPUT_FILE)