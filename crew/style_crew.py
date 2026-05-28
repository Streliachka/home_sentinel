from crewai import Crew, Process
from agents.style_agents import structure_scanner, photo_analyser, data_synthesizer, creative_director
from tasks.style_tasks import style_scan, style_analyze, style_report, style_final_guide
from tools.style_tools import scan_root_structure, analyze_photos_in_folder, read_profile_files

# Agents
structure_scanner_agent = structure_scanner
structure_scanner_agent.tools = [scan_root_structure]

photo_analyser_agent = photo_analyser
photo_analyser_agent.tools = [analyze_photos_in_folder]

data_synthesizer_agent = data_synthesizer
data_synthesizer_agent.tools = [read_profile_files]

creative_director_agent = creative_director

# Tasks
style_scan_task = style_scan
style_scan_task.agent = structure_scanner_agent

style_analyze_task = style_analyze
style_analyze_task.agent = photo_analyser_agent
style_analyze_task.context = [style_scan_task]

style_report_task = style_report
style_report_task.agent = data_synthesizer_agent
style_report_task.context = [style_analyze_task]

style_final_guide_task = style_final_guide
style_final_guide_task.agent = creative_director_agent
style_final_guide_task.context = [style_report_task]

photo_analysis_crew = Crew(
        agents=[structure_scanner_agent, photo_analyser_agent, data_synthesizer_agent, creative_director_agent],
        tasks=[style_scan_task, style_analyze_task, style_report_task, style_final_guide_task],
        process=Process.sequential,
        verbose=True
    )

#In main.py, after defining the crew and tasks, you can call the crew on a folder of images to process them and generate the style report and guide. For example:
# inputs = {
#         "root_directory": target_root_directory_goes_here
#     }
