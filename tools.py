# tools.py
import ipaddress
import re
import subprocess
import requests
from crewai.tools import tool
from typing import List

nmap_path = r"C:\Program Files (x86)\Nmap\nmap.exe"

@tool("scan_local_network")
def scan_network_logic(ip_range: str):
    """
    Scans the network and returns a CLEAN list of IPs, Hostnames, and Ports.
    """
    try:
        #result = subprocess.check_output([nmap_path, "-sn", ip_range], text=True)
        result = subprocess.check_output([nmap_path, "-sn", ip_range], text=True)
        return result
    except Exception as e:
        return f"Nmap error: {str(e)}"

@tool("get_mac_vendor")
def get_vendor_logic(mac_address: str):
    """
    Finds the manufacturer of a device using its MAC address.
    """
    try:
        response = requests.get(f"https://api.macvendors.com/{mac_address}", timeout=3)
        return response.text if response.status_code == 200 else "Unknown"
    except:
        return "Vendor lookup failed"
    
@tool("flexible_nmap")
def flexible_nmap(subnet: str, options: str = "-F"):
    """
    Safe Nmap wrapper for CrewAI agents.
    Allowed flags:
        -F
        -Pn
        -sV
        -O
        -T3, -T4, -T5
        --open
        --top-ports <1-999>
        -p <comma-separated ports 1-65535>
    Example:
        options="-Pn --top-ports 100"
    """

    # -----------------------------
    # 1. Validate subnet strictly
    # -----------------------------
    try:
        network = ipaddress.ip_network(subnet, strict=False)
    except ValueError:
        return "Error: Invalid IP address or CIDR range."

    # Optional: limit scan size (prevent /0 scans)
    if network.num_addresses > 4096:
        return "Error: Subnet too large. Maximum allowed size is 4096 hosts."

    # -----------------------------
    # 2. Tokenize safely
    # -----------------------------
    tokens = options.strip().split()
    if len(tokens) > 10:
        return "Error: Too many options supplied."

    # -----------------------------
    # 3. Allowed simple flags
    # -----------------------------
    simple_flags = {"-F", "-Pn", "-sV", "-O", "--open"}
    timing_pattern = re.compile(r"^-T[3-5]$")
    top_ports_pattern = re.compile(r"^\d{1,3}$")
    port_list_pattern = re.compile(r"^(\d{1,5})(,\d{1,5})*$")

    validated_args: List[str] = []

    i = 0
    while i < len(tokens):
        token = tokens[i]

        # ---- Simple flags
        if token in simple_flags:
            validated_args.append(token)

        # ---- Timing
        elif timing_pattern.fullmatch(token):
            validated_args.append(token)

        # ---- --top-ports N
        elif token == "--top-ports":
            if i + 1 >= len(tokens):
                return "Error: --top-ports requires a number."
            value = tokens[i + 1]
            if not top_ports_pattern.fullmatch(value):
                return "Error: Invalid value for --top-ports."
            if int(value) > 999:
                return "Error: --top-ports must be <= 999."
            validated_args.extend(["--top-ports", value])
            i += 1

        # ---- -p ports
        elif token == "-p":
            if i + 1 >= len(tokens):
                return "Error: -p requires a port list."
            ports = tokens[i + 1]
            if not port_list_pattern.fullmatch(ports):
                return "Error: Invalid port list format."

            # Validate each port
            for p in ports.split(","):
                if not (1 <= int(p) <= 65535):
                    return f"Error: Invalid port number {p}."

            validated_args.extend(["-p", ports])
            i += 1

        else:
            return f"Error: Invalid or unsupported option '{token}'."

        i += 1

    # -----------------------------
    # 4. Assemble safe command
    # -----------------------------
    command = [nmap_path] + validated_args + [str(network)]

    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=180,
            check=False
        )
        return result.stdout if result.stdout else result.stderr

    except subprocess.TimeoutExpired:
        return "Error: Scan timed out."
    except Exception as e:
        return f"Execution error: {str(e)}"
