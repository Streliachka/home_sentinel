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
    #output_json=FinalStockMetadata,   # Magic here: CrewAI will auto-format Agent 3 output using our Pydantic schema
)

task_format_data = Task(
    description="""You are given TWO inputs for the same stock image:
    1. ORIGINAL VISUAL FACTS (What is ACTUALLY in the image).
    2. RAW SEO & LEGAL OUTPUT (What the previous AI agents suggested based on business trends).
    
    Your job is to perform a strict compliance audit and formatting. Follow these microstock laws:
    
    LAW 1: THE TITLE RULE
    - Write a clean, natural English sentence (7-15 words).
    - Format: [Subject/Action] + [Environment/Context] + [Vibe/Season].
    - CRITICAL: Absolutely NO mathematical formulas, NO '+' signs, NO slashes, NO bullet points inside the title string. 
    - Example of a BAD title: 'Elevated Shot + Black Leather Outfit + Sitting/Relaxing'
    - Example of a GOOD title: 'Alternative young woman with pink hair in black leather outfit on winter balcony'
    
    LAW 2: THE KEYWORD ATOMIZATION RULE
    - Shutterstock searches rely on single words or very short, tight concepts (max 2 words, like 'leather jacket' or 'city view').
    - Take any long descriptive phrases from the RAW SEO output (e.g., 'pink hair modern style inspiration', 'cozy winter look on a balcony') and ATOMIZE them. Break them down into individual, clean keywords: ['pink hair', 'modern style', 'fashion', 'cozy', 'winter', 'balcony'].
    - Absolutely NO punctuation, NO full sentences, and NO words like 'and', 'with', 'on' inside the keywords array.
    
    LAW 3: THE ANTI-HALLUCINATION PURGE
    - Cross-check the RAW SEO keywords against the ORIGINAL VISUAL FACTS.
    - If the RAW SEO agent invented objects, actions, or concepts not supported by the visual facts (such as 'laptop', 'coffee', 'office', 'remote work setup', 'working from home' when there is only a balcony and a sunset), DELETE THEM IMMEDIATELY. Fake keywords lower the image's conversion rate and violate Shutterstock TOS.
    
    ---
    INPUT 1 (ORIGINAL VISUAL FACTS)
    INPUT 2 (RAW SEO & LEGAL OUTPUT)
    ---
    """,
    expected_output="A clean, optimized JSON object strictly matching the FinalStockMetadata schema.",
    #agent=metadata_formatter,
    #output_json=FinalStockMetadata
)