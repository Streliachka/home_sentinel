from crewai import Task


task_analyze_image = Task(
    description='''Analyze the image at path:{image_path}. 
        You MUST call tool analyze_image_via_ollama exactly once with {image_path}, {OLLAMA_HOST}, {OLLAMA_MODEL} and {PHOTO_INFO}. 
        The analysis model is always VISION_MODEL from environment; OLLAMA_MODEL input must not change image-analysis model selection.
        Do not output tool-call JSON in the final answer. 
        After the tool returns, identify main subject, secondary objects, shot angle, and environment.
       ''',
    expected_output="Description and a bullet-point list of literal visual facts present in the image.",
)

task_gen_description = Task(
    description="""Take the visual data from task task_analyze_image and create microstock metadata. 
    Targeted microstock is Shutterstock.
    MAIN TASK: Create a commercial title and a list of keywords that will maximize the image's conversion rate 
    on Shutterstock, while strictly following microstock rules.

    CRITICAL KEYWORD RULES:
    0. TARGET KEYWORD COUNT: return 35-50 keywords.
    1. Every keyword must be a SINGLE WORD (e.g., 'cyberpunk', 'boots', 'sunset') or a maximum of a 2-WORD PHRASE.
    2. Absolutely FORBIDDEN to use long descriptions, sentences, or phrases with the word 'and' inside the keywords array.
    3. Do NOT invent objects if they are not in the visual description.

    CRITICAL TITLE RULE:
    Write a clean, human-readable description. Do NOT use '+' signs or technical formulas.
    """,
    expected_output="A clean, optimized JSON object strictly matching the FinalStockMetadata schema.",
)

task_audit_description = Task(
    description="""You are given TWO inputs for the same stock image:
        1. ORIGINAL VISUAL FACTS (What is ACTUALLY in the image).
        2. RAW SEO & LEGAL OUTPUT (What the previous AI agents suggested based on business trends).

        Job is to perform a strict compliance audit and formatting.
        You can edit the title and keywords, but you CANNOT add new concepts that are not supported by the original visual facts.
        Feel free to EDIT the title to make it more compliant with microstock rules,
        but you cannot add new concepts to the title that are not supported by the original visual facts.
        Follow these microstock laws:

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

        LAW 4: THE KEYWORD COUNT RULE
        - Final keywords list must contain 35-50 keywords.
        - If the list is shorter, enrich it only with concepts directly supported by ORIGINAL VISUAL FACTS.
        - Never add concepts that are not visible in the image.

        ---
        INPUT 1 (ORIGINAL VISUAL FACTS)
        INPUT 2 (RAW SEO & LEGAL OUTPUT)
        ---
    """,
    expected_output="A clean, optimized JSON object strictly matching the FinalStockMetadata schema.",
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

    LAW 4: THE KEYWORD COUNT RULE
    - Final keywords list must contain 35-50 keywords.
    - If the list is shorter, enrich it only with concepts directly supported by ORIGINAL VISUAL FACTS.
    - Never add concepts that are not visible in the image.

    ---
    INPUT 1 (ORIGINAL VISUAL FACTS)
    INPUT 2 (RAW SEO & LEGAL OUTPUT)
    ---
    """,
    expected_output="A clean, optimized JSON object strictly matching the FinalStockMetadata schema.",
)
