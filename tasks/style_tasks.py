from crewai import Task

style_scan = Task(
    description='''Find all author subdirectories within the root directory '{root_directory}'. 
                    Based on the names of these folders, 
                    create individual files of the form 'AUTHOR_NAME_profile.json' inside '{style_data_dir}'.
                    Create '{style_data_dir}' if it does not exist.
                    You MUST call tool structure_scanning_tool exactly once with {root_directory} and {style_data_dir}.
                    Do not output tool-call JSON in the final answer.''',
    expected_output="List of created JSON files for each detected author in the selected style_data_dir workspace.",
    #agent=structure_scanner
)

style_analyze = Task(
    description='''Find all '*_profile.json' files in '{style_data_dir}'. 
                    For each file, run a deep photo analysis tool to extract EXIF data, 
                    analyze black color handling, contrast, minimalism and geometry in the Trashhand/FineArt style.
                    Include dominant colors as HEX values with approximate share and classify likely Itten color-wheel harmony. 
                    Rewrite these files by adding the extracted insights and an author-level style summary.
                    The summary must be saved in field 'author_style_profile' and must describe:
                    - artistic philosophy,
                    - likely author intentions,
                    - emotional and narrative direction,
                    - stylistic signature decisions (composition, light, color, processing).
                    You MUST call tool deep_photo_analyzer_tool exactly once with {style_data_dir}.
                    Do not output tool-call JSON in the final answer.''',
    expected_output="Updated author profile files containing deep technical/visual analysis and a detailed 'author_style_profile' section with philosophy and intentions.",
    #agent=photo_analyser
)

style_report = Task(
    description='''Read all updated '*_profile.json' files from '{style_data_dir}'. 
                    Conduct comparative analysis. 
                    Create a single report '{style_data_dir}/comprehensive_style_report.json'. 
                    Within the report, group data by patterns: whose shadows are matte, whose are crushed, which HEX palettes dominate, who exhibits minimalism and geometry.
                                        Add a cross-author color analytics section with:
                                        - recurring dominant HEX colors ranked by frequency,
                                        - recurring palette clusters (warm/cool/neutral families),
                                        - Itten color-wheel harmony frequencies across all analyzed photos
                                            (monochromatic, analogous, complementary, split complementary, triadic, tetradic, and contrast-based patterns),
                                        - per-author preferred harmony profile and notable deviations.
                    Also include a dedicated per-author section that summarizes each author's philosophy and intentions
                    (sourced from 'author_style_profile') and a cross-author comparison of these intentions.
                    You MUST call tool read_profile_files_tool exactly once with {style_data_dir}.
                    Do not output tool-call JSON in the final answer.''',
        expected_output="File 'comprehensive_style_report.json' containing common visual/technical patterns, aggregated HEX and Itten harmony statistics, plus per-author philosophy and intention summaries.",
    #agent=data_synthesizer,
    output_file="styleData/comprehensive_style_report.json"
)

style_final_guide = Task(
    description='''Read the final summary report '{style_data_dir}/comprehensive_style_report.json'. 
                    Write a detailed text manifesto and guide in English. 
                    The guide should contain 2 fundamental sections: 
                    1) How to shoot (Sony lens selection, working with geometry, angles and negative space in minimalist style), 
                    2) How to process in Lightroom (specific logic for channel calibration, curves, black point adjustment and HSL for obtaining steel tones). 
                    Save the guide to '{style_data_dir}/FINAL_PRO_PRODUCTION_GUIDE.md'.''',
    expected_output="File 'FINAL_PRO_PRODUCTION_GUIDE.md' with a detailed breakdown of steps from shooting to Lightroom slider adjustments.",
    #agent=creative_director,
    output_file="styleData/FINAL_PRO_PRODUCTION_GUIDE.md"
)