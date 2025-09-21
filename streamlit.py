import streamlit as st
import requests
import sseclient
import uuid
import json
import time
import datetime

st.set_page_config(page_title="Chatbot", page_icon="", layout="wide")
hide_streamlit_style = """
    <style>
    /* Ẩn header */
    header {visibility: hidden;}

    /* Ẩn footer */
    footer {visibility: hidden;}
    </style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)
BACKEND_URL = "https://chatbot-e5xc.onrender.com/chat"  # http://localhost:8080/-https://chatbot-e5xc.onrender.com/
if "uploader_key" not in st.session_state:
    st.session_state.uploader_key = 0
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
    "emotive",
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
    "emotive": "😊",
}

sidebar_container = st.sidebar.empty()


def render_sidebar():
    with sidebar_container.container():
        working_agent = st.session_state.get("working_agent")
        for agent in agents:
            icon = agent_icons.get(agent, "🔹")
            if agent == working_agent:
                st.markdown(f"### {agent.capitalize()} {icon}")
            else:
                st.markdown(f"{agent.capitalize()}")


st.session_state.update(
    {
        "session_id": st.session_state.get("session_id", str(uuid.uuid4())),
        "messages": st.session_state.get("messages", []),
        "working_agent": st.session_state.get("working_agent", None),
        "start_time_global": st.session_state.get("start_time_global", None),
        "total_time": st.session_state.get("total_time", 0.0),
    }
)

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

for msg in st.session_state.get("messages", []):
    with st.chat_message(msg.get("role", "assistant")):
        st.markdown(msg.get("content", ""))


uploaded_file = st.file_uploader(
    "file upload",
    type=["pdf", "docx"],
    accept_multiple_files=False,
    key=f"uploader_{st.session_state.uploader_key}",
)
if prompt := st.chat_input("enter..."):
    st.session_state["messages"].append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        placeholder = st.empty()
        full_response = ""

        with st.spinner("**Thinking**"):
            data = {"message": prompt}
            cookies = {"conversation_id": st.session_state.get("session_id")}
            if not uploaded_file:
                resp = requests.post(
                    BACKEND_URL,
                    data=data,
                    cookies=cookies,
                    stream=True,
                )
            else:
                resp = requests.post(
                    BACKEND_URL,
                    data=data,
                    files={
                        "file": (
                            uploaded_file.name,
                            uploaded_file,
                            uploaded_file.type,
                        )
                    },
                    cookies=cookies,
                    stream=True,
                )
                st.session_state.uploader_key += 1
            client = sseclient.SSEClient(resp)
            st.session_state["start_time_global"] = time.time()

        status_placeholder = st.empty()
        status_placeholder.markdown("**Responding**")
        for event in client.events():
            if not event.data:
                continue
            data = json.loads(event.data)
            if data.get("type") == "chunk":
                status_placeholder.markdown(f"**{data.get("agent").capitalize()}**")
                if data.get("agent") in agents:
                    st.session_state["working_agent"] = data.get("agent")
                    render_sidebar()
                if data.get("agent") in [
                    "analyst",
                    "calculator",
                    "coder",
                    "planner",
                    "search",
                    "tool",
                    "vision",
                    "writer",
                    "emotive",
                ]:
                    for char in data.get("response"):
                        time.sleep(10e-4)
                        full_response += char
                        placeholder.markdown(full_response)
            elif data.get("type") == "interrupt":
                if st.session_state.get("start_time_global"):
                    st.session_state["total_time"] = time.time() - st.session_state.get(
                        "start_time_global"
                    )
                break
            elif data.get("type") == "done":
                if st.session_state.get("start_time_global"):
                    st.session_state["total_time"] = time.time() - st.session_state.get(
                        "start_time_global"
                    )
                break

        st.session_state["working_agent"] = None
        render_sidebar()
        status_placeholder.markdown(f"*{st.session_state.get('total_time', 0.0):.2f}s*")
        st.session_state["total_time"] = 0.0
        st.session_state["messages"].append(
            {"role": "assistant", "content": full_response}
        )
