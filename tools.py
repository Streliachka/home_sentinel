# tools.py
import base64
import ipaddress
from pathlib import Path
import re
import subprocess
import requests
from crewai.tools import tool
from typing import List

#nmap_path = r"C:\Program Files (x86)\Nmap\nmap.exe"
nmap_path = "nmap"

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
    

@tool("analyze_image_via_ollama")
def analyze_image_via_ollama(image_path: str, OLLAMA_HOST: str, OLLAMA_MODEL: str, PHOTO_INFO: str = None) -> str:
    """
    Analyze the image at image_path using Ollama and return a detailed literal description.
    Accepts optional PHOTO_INFO string containing extra metadata for matching files.
    """
    try:
        current_filename = Path(image_path).stem
        additional_context = ""
        
        # 1. Быстрая проверка: если PHOTO_INFO пустой/null или имени файла в нем вообще нет — полностью игнорируем парсинг
        if PHOTO_INFO and str(PHOTO_INFO).strip() and (current_filename in PHOTO_INFO):
            
            # 2. Только если имя файла нашлось как подстрока, парсим всю структуру
            extra_info_dict = {}
            pairs = PHOTO_INFO.split(';')
            for pair in pairs:
                if '=' in pair:
                    filename, info = pair.split('=', 1)
                    extra_info_dict[filename.strip()] = info.strip()

            # Достаем точный контекст именно для текущего файла
            additional_context = extra_info_dict.get(current_filename, "")

        # 3. Формируем базовый промпт для модели
        base_prompt = "Describe this image in detail for a microstock presentation. What objects, colors, and potential trademark risks do you see?"
        
        # Добавляем контекст, только если он был успешно найден
        if additional_context:
            base_prompt += f"\n\nAdditional context or user notes for this specific image: {additional_context}"

        # Читаем изображение и кодируем в base64
        with open(image_path, "rb") as f:
            img_str = base64.b64encode(f.read()).decode('utf-8')

        # Прогрев модели (Warm up) для загрузки в память Ollama
        warmup_payload = {
            "model": OLLAMA_MODEL,
            "prompt": "ping",
            "stream": False,
            "options": {"num_predict": 1},
            "keep_alive": "10m"
        }
        
        warmup_response = requests.post(
            f"{OLLAMA_HOST}/api/generate",
            json=warmup_payload,
            timeout=60
        )
        if warmup_response.status_code != 200:
            return f"Error loading model in Ollama: {warmup_response.text}"
            
        # Основной запрос к Ollama API
        payload = {
            "model": OLLAMA_MODEL,
            "prompt": base_prompt,
            "stream": False,
            "images": [img_str]
        }
        
        response = requests.post(
            f"{OLLAMA_HOST}/api/generate",
            json=payload,
            timeout=180
        )
        
        if response.status_code == 200:
            return response.json().get("response", "No response from model.")
        return f"Error from Ollama: {response.text}"

    except requests.exceptions.RequestException as e:
        return f"Ollama API request failed: {str(e)}"
    except Exception as e:
        return f"Failed to process image: {str(e)}"
