import subprocess
import requests
from langchain.tools import tool

class NetworkTools:
    
    @tool("scan_local_network")
    def scan_network(ip_range: str):
        """
        Scans the local network using nmap to find active hosts.
        Returns raw nmap output containing IP and MAC addresses.
        """
        try:
            # -sn: Ping scan (disable port scan), -n: Skip DNS resolution for speed
            result = subprocess.check_output(["nmap", "-sn", ip_range], text=True)
            return result
        except Exception as e:
            return f"Error executing nmap: {str(e)}"

    @tool("get_mac_vendor")
    def get_mac_vendor(mac_address: str):
        """
        Takes a MAC address and returns the manufacturer name (e.g., Apple, Samsung).
        Helps identify the type of device connected to the network.
        """
        try:
            # Using a public API to resolve MAC to Vendor
            response = requests.get(f"https://api.macvendors.com/{mac_address}", timeout=3)
            if response.status_code == 200:
                return response.text
            return "Unknown Vendor"
        except Exception as e:
            return f"Vendor lookup failed: {str(e)}"