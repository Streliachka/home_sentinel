import os
from crewai import LLM, Agent
from dotenv import load_dotenv
from tools.tools import scan_network_logic, get_vendor_logic, flexible_nmap

load_dotenv()

OLLAMA_HOST = os.getenv("OLLAMA_BASE_URL")
VISION_MODEL = os.getenv("VISION_MODEL")
LOCAL_MODEL = os.getenv("LOCAL_MODEL")

LOCAL_MODEL_OBJ = LLM(
    model=LOCAL_MODEL, 
    base_url=OLLAMA_HOST,
    temperature=0.2
)

# VISION_MODEL_OBJ = LLM(
#     model=VISION_MODEL, 
#     base_url=OLLAMA_HOST
# )

#----------------------------------------------------- Network Security Agents -----------------------------------------------------

watcher = Agent(
    role='Network Security Specialist',
    goal='''Scan the subnet {subnet} and identify all devices. Some IoT devices might be in sleep mode.''',
    backstory='You are a cyber-security expert guarding a home network.',
    tools=[scan_network_logic, flexible_nmap],
    llm=LOCAL_MODEL_OBJ,
    verbose=True,
    max_iter=5,
    allow_delegation=False
)

analyst = Agent(
    role='Cybersecurity Risk Analyst',
    goal='Analyze raw network data to identify potential threats and organize information.',
    backstory='You are a certified security auditor. You look at open ports and device names to find vulnerabilities.',
    llm=LOCAL_MODEL_OBJ,
    verbose=True
)

suggestor = Agent (
    role="Cybersecurity trouble shooter",
    goal='''Suggest actions based on the analysis. 
            Read recommendations from the analyst. 
            Evaluate how usefull suggestions are from analyst and make decisions. Whether actions are needed.''',
    backstory='You are a cybersecurity expert who has been trained to suggest solutions for potential threats.',
    llm=LOCAL_MODEL_OBJ,
    verbose=True
)