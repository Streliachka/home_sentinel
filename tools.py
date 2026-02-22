# tools.py
import subprocess
import requests
from crewai.tools import tool

@tool("scan_local_network")
def scan_network_logic(ip_range: str):
    """
    Scans the network and returns a CLEAN list of IPs, Hostnames, and Ports.
    """
    try:
        nmap_path = r"C:\Program Files (x86)\Nmap\nmap.exe" 
        #result = subprocess.check_output([nmap_path, "-sn", ip_range], text=True)
        result = subprocess.check_output([nmap_path, "-PR", "-sn", ip_range], text=True)
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