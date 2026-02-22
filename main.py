import os

# 1. Настройки окружения
os.environ["CREWAI_TELEMETRY_OPT_OUT"] = "true"
# LiteLLM иногда все равно ищет ключ, дадим ему любой текст
os.environ["OPENAI_API_KEY"] = "sk-ollama-local" 

from crewai import Agent, Task, Crew, Process
from tools import scan_network_logic, get_vendor_logic

# 2. Нативная модель
LOCAL_MODEL = "ollama/llama3.1:8b"

# 3. Агент
watcher = Agent(
    role='Network Security Specialist',
    goal='Scan the subnet {subnet} and identify all devices.',
    backstory='You are a cyber-security expert guarding a home network.',
    tools=[scan_network_logic, get_vendor_logic],
    llm=LOCAL_MODEL,
    verbose=True,
    allow_delegation=False
)

# 4. Задача
scan_task = Task(
    description='1. Scan {subnet} using nmap. 2. For each MAC, find vendor. 3. Return a table.',
    expected_output='Markdown table with IP, MAC, and Vendor.',
    agent=watcher
)

# 5. Команда
sentinel_crew = Crew(
    agents=[watcher],
    tasks=[scan_task],
    process=Process.sequential
)

if __name__ == "__main__":
    print("\n--- [AGENT IS WAKING UP] ---")
    # Убедись, что Ollama запущена в фоне!
    sentinel_crew.kickoff(inputs={'subnet': '192.168.0.0/24'})