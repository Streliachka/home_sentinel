import os
from crewai import Agent, Task, Crew, Process
from langchain_community.llms import Ollama
from tools import NetworkTools

# 1. Setting up local model (Ollama)
# Make sure you've done `ollama pull llama3`
llm = Ollama(model="llama3", base_url="http://localhost:11434")

# 2. Creating an Agent
watcher = Agent(
    role='Network Security Specialist',
    goal='Scan the network {subnet}, match MAC addresses with vendors, and identify suspicious devices.',
    backstory='You are a domestic AI guardian. Your task is to ensure that only familiar devices (e.g., your laptop, phone, router) are in the network. If you see a new device from an unknown vendor - it\'s reason for concern.',
    tools=[NetworkTools.scan_network, NetworkTools.get_mac_vendor],
    llm=llm,
    verbose=True
)

# 3. Task to perform
scan_task = Task(
    description='Perform a network scan of {subnet}. For each found MAC address, find the vendor. Create a list: IP - MAC - Vendor.',
    expected_output='Table with a list of all devices and final conclusion: is there anyone else in the network?',
    agent=watcher
)

# 4. Forming a crew
sentinel_crew = Crew(
    agents=[watcher],
    tasks=[scan_task],
    process=Process.sequential
)

# 5. Let's go!
if __name__ == "__main__":
    print("--- Starting Domestic Guardian ---")
    result = sentinel_crew.kickoff(inputs={'subnet': '192.168.0.0/24'})
    print("\n\n########################")
    print("## GUARDIAN REPORT: ")
    print(result)