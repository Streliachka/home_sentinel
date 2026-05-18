from crewai import Agent
from tools import scan_network_logic, get_vendor_logic, flexible_nmap

LOCAL_MODEL = "ollama/llama3.1:8b"

watcher = Agent(
    role='Network Security Specialist',
    goal='''Scan the subnet {subnet} and identify all devices. Some IoT devices might be in sleep mode.''',
    backstory='You are a cyber-security expert guarding a home network.',
    tools=[scan_network_logic, flexible_nmap],
    llm=LOCAL_MODEL,
    verbose=True,
    max_iter=5,
    allow_delegation=False
)

analyst = Agent(
    role='Cybersecurity Risk Analyst',
    goal='Analyze raw network data to identify potential threats and organize information.',
    backstory='You are a certified security auditor. You look at open ports and device names to find vulnerabilities.',
    llm=LOCAL_MODEL,
    verbose=True
)

suggestor = Agent (
    role="Cybersecurity trouble shooter",
    goal="Suggest actions based on the analysis. Read recommendations from the analyst. Evaluate how usefull suggestions are from analyst and make decisions. Whether actions are needed.",
    backstory='You are a cybersecurity expert who has been trained to suggest solutions for potential threats.',
    llm=LOCAL_MODEL,
    verbose=True
)