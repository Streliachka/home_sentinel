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