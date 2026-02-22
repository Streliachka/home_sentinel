from crewai import Agent
from langchain_community.llms import Ollama
from tools import NetworkTools

# Connect to local Ollama instance
local_llm = Ollama(model="llama3", base_url="http://localhost:11434")

# Network Watcher Agent
watcher = Agent(
    role='Network Guardian',
    goal='Analyze network scanning reports and detect suspicious activity in subnet {subnet}',
    backstory='You are a cybersecurity expert. You know all home devices and immediately notice intruders.',
    tools=[NetworkTools.scan_network],
    llm=local_llm,
    verbose=True
)