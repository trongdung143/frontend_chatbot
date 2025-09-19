import streamlit as st
import requests
import sseclient
import uuid
import json
import time
import datetime

st.set_page_config(page_title="Chatbot", page_icon="", layout="wide")

BACKEND_URL = "https://chatbot-e5xc.onrender.com/chat"  # http://localhost:8080/

agents = [
    "analyst",
    "assigner",
    "calculator",
    "coder",
    "memory",
    "planner",
    "search",
    "supervisor",
    "tool",
    "vision",
    "writer",
]

agent_icons = {
    "analyst": "📊",
    "assigner": "📌",
    "calculator": "🧮",
    "coder": "💻",
    "memory": "🧠",
    "planner": "🗓️",
    "search": "🔍",
    "supervisor": "👨‍💼",
    "tool": "🛠️",
    "vision": "👁️",
    "writer": "✍️",
}

sidebar_container = st.sidebar.empty()


def render_sidebar():
    with sidebar_container.container():
        working_agent = st.session_state.get("working_agent", None)
        for agent in agents:
            icon = agent_icons.get(agent, "🔹")
            if agent == working_agent:
                st.markdown(f"**{agent.capitalize()}**")
            else:
                st.markdown(f"{agent.capitalize()}")


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
    st.session_state.update(
        {
            "messages": [],
            "total_time": 0.0,
            "start_time_global": None,
            "working_agent": None,
            "last_reset": today,
        }
    )

render_sidebar()

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("enter..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        placeholder = st.empty()
        full_response = ""

        with st.spinner("*Thinking*"):
            data = {"message": prompt}
            cookies = {"conversation_id": st.session_state.session_id}
            resp = requests.post(BACKEND_URL, data=data, cookies=cookies, stream=True)
            client = sseclient.SSEClient(resp)
            st.session_state.start_time_global = time.time()

        status_placeholder = st.empty()
        status_placeholder.markdown("*Responding*")
        for event in client.events():
            if not event.data:
                continue
            data = json.loads(event.data)

            if data["type"] == "status":
                st.session_state.working_agent = data["agent"]
                render_sidebar()
                status_placeholder.markdown(f"*Responding of {data['agent']}...*")

            elif data["type"] == "chunk":
                for char in data["response"]:
                    time.sleep(10e-4)
                    full_response += char
                    placeholder.markdown(full_response)

            elif data["type"] == "done":
                if st.session_state.start_time_global:
                    st.session_state.total_time = (
                        time.time() - st.session_state.start_time_global
                    )
                break

        st.session_state.working_agent = None
        status_placeholder.markdown(f"*{st.session_state.total_time:.2f}s*")
        st.session_state.total_time = 0.0
        render_sidebar()
        st.session_state.messages.append(
            {"role": "assistant", "content": full_response}
        )
