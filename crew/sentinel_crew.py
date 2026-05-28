from crewai import Crew, Process

from agents.sentinel_agents import watcher, analyst, suggestor
from tasks.sentinel_tasks import scan, analyze, suggest


scan_task = scan
scan_task.agent = watcher

analyze_task = analyze
analyze_task.agent = analyst
analyze_task.context = [scan_task]

suggest_task = suggest
suggest_task.agent = suggestor
suggest_task.context = [analyze_task]


sentinel_crew = Crew(
	agents=[watcher, analyst, suggestor],
	tasks=[scan_task, analyze_task, suggest_task],
	process=Process.sequential,
	verbose=True,
)
