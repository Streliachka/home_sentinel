import os
from crewai import LLM, Agent
from shared.llm_config import get_base_llms

llms = get_base_llms()

def _build_style_agent_llm() -> LLM:
    provider = (os.getenv("STYLE_AGENT_PROVIDER") or "ollama").strip().lower()
    style_model = (os.getenv("STYLE_AGENT_MODEL") or "").strip()

    if provider == "gemini":
        model_name = style_model or (os.getenv("GEMINI_MODEL") or "").strip()
        if not model_name:
            raise ValueError("STYLE_AGENT_MODEL or GEMINI_MODEL is required when STYLE_AGENT_PROVIDER=gemini")
        gemini_api_key = os.getenv("GEMINI_API_KEY")
        if not gemini_api_key:
            raise ValueError("GEMINI_API_KEY is required when STYLE_AGENT_PROVIDER=gemini")
        return LLM(
            model=model_name,
            temperature=0.2,
            api_key=gemini_api_key,
        )

    model_name = style_model or (os.getenv("LOCAL_MODEL") or "").strip() or (os.getenv("LOCAL_MODEL_PLUS") or "").strip() or (os.getenv("VISION_MODEL") or "").strip()
    if not model_name:
        raise ValueError(
            "STYLE_AGENT_MODEL or LOCAL_MODEL or LOCAL_MODEL_PLUS or VISION_MODEL is required when STYLE_AGENT_PROVIDER=ollama"
        )
    if "/" not in model_name:
        model_name = f"ollama/{model_name}"
    ollama_host = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    return LLM(
        model=model_name,
        base_url=ollama_host,
        temperature=0.2,
    )

STYLE_AGENT_LLM = _build_style_agent_llm()

structure_scanner = Agent(
    role="File System Data Structure Specialist",
    goal="Clearly define the root folder structure, identify author names, and initialize reporting JSON documents.",
    backstory='''Expert system archivist. Master of working with file system data structures,
                 turning the chaos of directories into ordered entities.''',
    #tools=[scan_root_structure],
    verbose=True,
    llm=STYLE_AGENT_LLM,
)

# Agent 2: AI Art Director (Pixel Analyzer)
photo_analyser = Agent(
    role="Expert in Technical and Artistic Photo Analysis",
    goal='''Methodically extract EXIF data and conduct deep visual analysis of tones,
            composition and color of each photo, enriching author profiles.''',
    backstory='''Former chief critic of Fine Art gallery and technical specialist in digital signal processing.
            Sees histogram, contrast curves and frame geometry through pixels.''',
    #tools=[analyze_photos_in_folder],
    verbose=True,
    llm=STYLE_AGENT_LLM,
)

# Agent 3: Analyst-Summarizer (Data Miner)
data_synthesizer = Agent(
    role="Chief Data Analyst for Art Projects",
    goal='''Study detailed JSON profiles of all authors and form one consolidated analytical JSON report
            with comparative trend analysis.''',
    backstory='''Specialist in Big Data in the media industry. Able to combine scattered patterns
            of hundreds of files into a single structured picture of dependencies.''',
    #tools=[DirectoryReadTool(directory="./")], # Reads JSON files in project root
    verbose=True,
    llm=STYLE_AGENT_LLM,
)

# Agent 4: Photography Industry Strategist (Editor-in-Chief)
creative_director = Agent(
    role="Creative Director and Curator of Photo Exhibitions",
    goal='''Based on the summary report, compile a final guide, detailed recommendations
        and roadmap for reproducing these styles at the shooting and post-processing stages.''',
    backstory='''Legendary mentor who raised dozens of top commercial and fine art photographers.
        Knows how to turn dry chart numbers into concrete camera hand positions and Adobe Lightroom sliders.''',
    verbose=True,
    llm=STYLE_AGENT_LLM,
)