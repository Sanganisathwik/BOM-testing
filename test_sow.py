import requests
import json

url = 'http://localhost:8000/api/generate-sow/chat/'
data = {
    "text": """we will type in chat below details .so we have to get the attached document
1. 📌 Overview
This document outlines the high-level network design for a new office in London supporting:
100 users (wired/wireless)
20 IP Phones
20 Wireless Access Points
30 additional devices (printers, CCTV, IoT, etc.)
2. 🎯 Design Objectives
Scalable (future growth to ~200 users)
High availability (no single point of failure)
Secure segmentation (data, voice, guest, IoT)
Optimized for collaboration (VoIP, Wi-Fi)
Cisco-based enterprise architecture"""
}

try:
    print("Sending request to:", url)
    response = requests.post(url, json=data)
    print("Status Code:", response.status_code)
    try:
        res_json = response.json()
        print("Response JSON:")
        print(json.dumps(res_json, indent=2))
    except Exception:
        print("Raw Response:", response.text)
except Exception as e:
    print("Error:", e)
