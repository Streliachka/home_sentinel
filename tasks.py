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
    description="Analyze the image at path:{image_path}. You MUST call tool analyze_image_via_ollama exactly once with {image_path}, {OLLAMA_HOST}, and {OLLAMA_MODEL}. Do not output tool-call JSON in the final answer. After the tool returns, identify main subject, secondary objects, shot angle, and environment.",
    expected_output="Description and a bullet-point list of literal visual facts present in the image.",
)

task_gen_description = Task(
    description="""Take the visual data from Task 1 and create microstock metadata. Targeted microstock is Shutterstock.
    
    CRITICAL KEYWORD RULES:
    1. Every keyword must be a SINGLE WORD (e.g., 'cyberpunk', 'boots', 'sunset') or a maximum of a 2-WORD PHRASE.
    2. Absolutely FORBIDDEN to use long descriptions, sentences, or phrases with the word 'and' inside the keywords array.
    3. Do NOT invent objects if they are not in the visual description.
    
    CRITICAL TITLE RULE:
    Write a clean, human-readable description. Do NOT use '+' signs or technical formulas.
    """,
    expected_output="An initial metadata structure with a title and keywords.",
)

task_audit_description = Task(
    description="Audit the title and keywords. Remove all brand names/trademarks. Clean up all formatting.",
    expected_output="The final audited stock metadata package.",
    #output_json=FinalStockMetadata,   #!!! МАГИЯ ТУТ: CrewAI сам отформатирует вывод Агента 3 по нашей Pydantic схеме
)