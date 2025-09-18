import streamlit as st
import requests
import sseclient
import uuid
import json
import time
import datetime

st.set_page_config(page_title="Chatbot", page_icon="", layout="wide")

BACKEND_URL = "https://chatbot-e5xc.onrender.com/chat"

agents = [
    "analyst","assigner","calculator","coder","memory",
    "planner","search","supervisor","tool","vision","writer",
]

agent_icons = {
    "analyst": "📊","assigner": "📌","calculator": "🧮","coder": "💻",
    "memory": "🧠","planner": "🗓️","search": "🔍","supervisor": "👨‍💼",
    "tool": "🛠️","vision": "👁️","writer": "✍️",
}

sidebar_container = st.sidebar.empty()

def render_sidebar():
    with sidebar_container.container():
        working_agent = st.session_state.get("working_agent", None)
        for agent in agents:
            icon = agent_icons.get(agent, "🔹")
            if agent == working_agent:
                st.markdown(f"**{icon} {agent.capitalize()} ⏳**")
            else:
                st.markdown(f"{icon} {agent.capitalize()}")
        st.markdown(f"{st.session_state.total_time:.2f}s")
        st.divider()

if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if "messages" not in st.session_state:
    st.session_state.messages = []
if "working_agent" not in st.session_state:
    st.session_state.working_agent = None
if "start_time_global" not in st.session_state:
    st.session_state.start_time_global = None
if "total_time" not in st.session_state:
    st.session_state.total_time = 0.0

today = str(datetime.date.today())
if st.session_state.get("last_reset") != today:
    st.session_state.update({
        "messages": [],
        "total_time": 0.0,
        "start_time_global": None,
        "working_agent": None,
        "last_reset": today
    })

render_sidebar()

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("enter ..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        placeholder = st.empty()
        full_response = ""

        with st.spinner("thinking ..."):
            data = {"message": prompt}
            cookies = {"session_id": st.session_state.session_id}
            resp = requests.post(BACKEND_URL, data=data, cookies=cookies, stream=True)
            client = sseclient.SSEClient(resp)
            st.session_state.start_time_global = time.time()

    with st.spinner("responding ...")

        for event in client.events():
            if not event.data:
                continue
            data = json.loads(event.data)

            if data["type"] == "status":
                st.session_state.working_agent = data["agent"]
                render_sidebar()

            elif data["type"] == "chunk":
                full_response += data["response"]
                placeholder.markdown(full_response)

            elif data["type"] == "done":
                if st.session_state.start_time_global:
                    st.session_state.total_time = time.time() - st.session_state.start_time_global
                break

            elif data["type"] == "error":
                placeholder.error(data["message"])
                break

        st.session_state.working_agent = None
        render_sidebar()
        st.session_state.messages.append({"role": "assistant", "content": full_response})