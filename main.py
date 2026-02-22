import os

# 1. Настройки окружения
os.environ["CREWAI_TELEMETRY_OPT_OUT"] = "true"
os.environ["OPENAI_API_KEY"] = "sk-ollama-local" 

from crewai import Agent, Task, Crew, Process
from tools import scan_network_logic, get_vendor_logic, flexible_nmap

# Нативная модель
LOCAL_MODEL = "ollama/llama3.1:8b"

# Агент
watcher = Agent(
    role='Network Security Specialist',
    goal='''Scan the subnet {subnet} and identify all devices. Some IoT devices might be in sleep mode. ''',
    backstory='You are a cyber-security expert guarding a home network.',
    #tools=[scan_network_logic, get_vendor_logic],
    tools=[scan_network_logic, flexible_nmap],
    llm=LOCAL_MODEL,
    verbose=True,
    max_iter=3,
    allow_delegation=False
)

# Analyst
analyst = Agent(
    role='Cybersecurity Risk Analyst',
    goal='Analyze raw network data to identify potential threats and organize information. ',
    backstory='You are a certified security auditor. You look at open ports and device names to find vulnerabilities.',
    llm=LOCAL_MODEL,
    verbose=True
)

# Задача 
task_scan = Task(
    description='Scan the network {subnet}. Focus on finding every active IP and all their open ports. Your ultimate goal is to find all active devices.',
    expected_output='A raw list of devices with their IPs, MACs, and open ports string.',
    agent=watcher
)

task_analyze = Task(
    description='''Review the raw scan data. 
    1. Identify what kind of device each one is (e.g., IoT, PC, Router).
    2. Analyze open ports: are they dangerous? (e.g. port 23/Telnet is bad).
    3. Create a final professional Markdown table.''',
    expected_output='''A final security report in Markdown:
    - Summary of the network health.
    - Table: Device | IP | Open Ports | Risk Level | Recommendation.''',
    agent=analyst,
    context=[task_scan] # Явно указываем, что аналитик ждет данные от сканера
)

# 5. Команда
sentinel_crew = Crew(
    agents=[watcher, analyst],
    tasks=[task_scan, task_analyze],
    process=Process.sequential
)

if __name__ == "__main__":
    print("\n--- [AGENT IS WAKING UP] ---")
    # Убедись, что Ollama запущена в фоне!
    sentinel_crew.kickoff(inputs={'subnet': '192.168.0.0/24'})