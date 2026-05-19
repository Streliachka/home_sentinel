# This script simulates a security task force that includes two agents: a Network Security Specialist and a Cybersecurity Risk Analyst.
# The goal of this exercise is to demonstrate how these agents can work together to analyze network data and identify potential threats.

# Import necessary libraries and modules
import os


from tools import analyze_image_via_ollama

# Set environment variables for telemetry and API key settings
os.environ["CREWAI_TELEMETRY_OPT_OUT"] = "true"
os.environ["OPENAI_API_KEY"] = "sk-ollama-local" 

# Import the required classes from the crewai library
from crewai import Crew, Process, Task, LLM
from agents import visual_analyst, seo_strategist, legal_auditor
from tasks import task_analyze_image,task_gen_description, task_audit_description
from pydantic import BaseModel, Field

# Set default Ollama host URL to localhost if not set in environment variables
OLLAMA_HOST = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
LOCAL_MODEL = "ollama/llama3.2:3b"
#VISION_MODEL = "ollama/llava:7b"
VISION_MODEL = "ollama/moondream:latest"

os.environ["OLLAMA_BASE_URL"] = OLLAMA_HOST

class FinalStockMetadata(BaseModel):
    status: str = Field(description="Must be 'CLEANED_AND_APPROVED'")
    modifications_made: str = Field(description="What trademarks or spam words were removed or altered")
    title: str = Field(description="Legally safe, commercially optimized English title (7-15 words)")
    keywords: list[str] = Field(description="Array of 35-45 clean, relevant, lowercase keywords")

LOCAL_MODEL_OBJ = LLM(
    model=LOCAL_MODEL, 
    base_url=OLLAMA_HOST
)

VISION_MODEL_OBJ = LLM(
    model=VISION_MODEL, 
    base_url=OLLAMA_HOST
)

# Agents
visual_analyst_agent = visual_analyst
visual_analyst_agent.llm = LOCAL_MODEL_OBJ
visual_analyst_agent.tools = [analyze_image_via_ollama]

seo_strategist_agent = seo_strategist
seo_strategist_agent.llm = LOCAL_MODEL_OBJ

legal_auditor_agent = legal_auditor
legal_auditor_agent.llm = LOCAL_MODEL_OBJ

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

shutter_crew = Crew(
    agents=[visual_analyst_agent, seo_strategist_agent, legal_auditor_agent],
    tasks=[taskAnalyzeImage, taskGenDescription, taskAuditDescription],
    process=Process.sequential,
    verbose=True
    )
    
if __name__ == "__main__":
    image_path = r"C:\Users\oprokopenko\Dropbox\Actum\Photo\hnt\28.jpg"
    test_inputs = {
            "image_path": image_path,
            "OLLAMA_HOST": OLLAMA_HOST,
            "OLLAMA_MODEL": VISION_MODEL,
        }

    print("Starting local Microstock CrewAI Factory...")
    result = shutter_crew.kickoff(inputs=test_inputs)

    print("\nFINAL LEGALLY SAFE METADATA RESULT:")
    print(result)