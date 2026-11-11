import json
import os
import shutil
import subprocess
import sys
import urllib.request
import streamlit as st

st.set_page_config(page_title="Xiaozhi Tuya MCP Bridge", page_icon="🔌")

REQUIRED_KEYS = [
    "MCP_ENDPOINT",
    "TUYA_ACCESS_ID",
    "TUYA_ACCESS_KEY",
    "TUYA_API_ENDPOINT",
]

missing_keys = [k for k in REQUIRED_KEYS if k not in st.secrets]
if missing_keys:
    st.error(f"Missing Streamlit Secrets: {', '.join(missing_keys)}")
    st.stop()

for key in REQUIRED_KEYS:
    os.environ[key] = st.secrets[key]


@st.cache_resource
def start_mcp_bridge():
    # Download the official Xiaozhi WebSocket MCP pipe script
    urllib.request.urlretrieve(
        "https://raw.githubusercontent.com/78/mcp-calculator/main/mcp_pipe.py",
        "mcp_pipe.py",
    )

    # Resolve the full path to mcp-server-tuya inside the Streamlit virtualenv
    tuya_cmd = shutil.which("mcp-server-tuya") or "mcp-server-tuya"

    # Generate mcp_config.json with injected Tuya environment variables
    mcp_config = {
        "mcpServers": {
            "tuya": {
                "type": "stdio",
                "command": tuya_cmd,
                "args": [],
                "env": {
                    "TUYA_ACCESS_ID": st.secrets["TUYA_ACCESS_ID"],
                    "TUYA_ACCESS_KEY": st.secrets["TUYA_ACCESS_KEY"],
                    "TUYA_API_ENDPOINT": st.secrets["TUYA_API_ENDPOINT"],
                },
                "disabled": False,
            }
        }
    }
    with open("mcp_config.json", "w", encoding="utf-8") as f:
        json.dump(mcp_config, f, indent=2)

    # Start mcp_pipe.py in the background
    return subprocess.Popen([sys.executable, "mcp_pipe.py"])


proc = start_mcp_bridge()

st.title("Xiaozhi ↔ Tuya Cloud MCP Bridge")
is_running = proc.poll() is None

if is_running:
    st.success(f"Bridge Running (PID: {proc.pid}) — Connected to xiaozhi.me")
else:
    st.warning(f"Bridge process exited with code {proc.returncode}")

if st.button("Restart MCP Bridge"):
    if proc.poll() is None:
        proc.terminate()
    st.cache_resource.clear()
    st.rerun()
