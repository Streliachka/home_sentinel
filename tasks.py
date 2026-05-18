from crewai import Task

scan = Task(
    description='Scan the network {subnet}. Focus on finding every active IP and all their open ports. Your ultimate goal is to find all active devices.',
    expected_output='A raw list of devices with their IPs, MACs, and open ports string.',
)

suggest = Task(
    description='Analyze suggestions and give your evaluation. Explain if actions are needed. If actions are needed, explain.',
    expected_output='Suggestions with explanations if actions really needed.',
)

analyze = Task(
    description='''
    Review the raw scan data.
    1. Identify what kind of device each one is (e.g., IoT, PC, Router).
    2. Analyze open ports: are they dangerous? (e.g. port 23/Telnet is bad).
    3. Create a final professional Markdown table.''',
    expected_output='''
        A final security report in Markdown:
        - Summary of the network health.
        - Table: Device | IP | Open Ports | Risk Level | Recommendation.''',
)

task_analyze_image = Task(
    description="Analyze the image at {image_path}. Identify the main subject, secondary objects, shot angle, and environment.",
    expected_output="Description and a bullet-point list of literal visual facts present in the image.",
)

task_gen_description = Task(
    description="Take visual facts and generate a commercial title (7-15 words) and 40 relevant keywords. Focus on business value and buyer intent.",
    expected_output="An initial metadata structure with a title and keywords.",
)

task_audit_description = Task(
    description="Audit the title and keywords. Remove all brand names/trademarks. Ensure that if 'Prague' is in the text, tags like 'Czech Republic, Europe' are added. Clean up all formatting.",
    expected_output="The final audited stock metadata package.",
    #output_json=FinalStockMetadata,   #!!! МАГИЯ ТУТ: CrewAI сам отформатирует вывод Агента 3 по нашей Pydantic схеме
)