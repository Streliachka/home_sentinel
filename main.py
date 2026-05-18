# This script simulates a security task force that includes two agents: a Network Security Specialist and a Cybersecurity Risk Analyst.
# The goal of this exercise is to demonstrate how these agents can work together to analyze network data and identify potential threats.

# Import necessary libraries and modules
import os

# Set environment variables for telemetry and API key settings
os.environ["CREWAI_TELEMETRY_OPT_OUT"] = "true"
os.environ["OPENAI_API_KEY"] = "sk-ollama-local" 

# Import the required classes from the crewai library
from crewai import Crew, Process, Task
from agents import watcher, analyst, suggestor
from tasks import scan, analyze, suggest

# Import necessary tools for network scanning and analysis
from tools import scan_network_logic, get_vendor_logic, flexible_nmap

# Set default Ollama host URL to localhost if not set in environment variables
OLLAMA_HOST = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
LOCAL_MODEL = "ollama/llama3.1:8b"
os.environ["OLLAMA_BASE_URL"] = OLLAMA_HOST

# Define the Network Security Specialist agent
watcherAgent = watcher

# Define the Cybersecurity Risk Analyst agent
analystAgent = analyst
suggestAgent = suggestor

# Define the scan task for the Network Security Specialist agent
scan.agent = watcherAgent
task_scan_updated = scan

# Define the analyze task for the Cybersecurity Risk Analyst agent
task_analyze_updated = suggest
analyze.agent = analystAgent
analyze.context = [task_scan_updated] # The analyst depends on the data from the scanner

task_suggest_updated = suggest
task_suggest_updated.agent = suggestAgent
task_suggest_updated.context = [task_analyze_updated]

# Define the crew that includes both agents and tasks
sentinel_crew = Crew(
    agents=[watcherAgent, analystAgent, suggestAgent],
    tasks=[task_scan_updated, task_analyze_updated, task_suggest_updated],
    process=Process.sequential
)

if __name__ == "__main__":
    print("\n--- [AGENT IS WAKING UP] ---")
    # Ensure Ollama is running in the background!
    sentinel_crew.kickoff(inputs={'subnet': '192.168.0.0/24'})