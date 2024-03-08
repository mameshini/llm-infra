import os
import streamlit as st
from streamlit_pills import pills
from llama_index import download_loader

from st_utils import (
    add_builder_config,
    add_sidebar,
    get_current_state,
)

current_state = get_current_state()

####################
#### STREAMLIT #####
####################


st.set_page_config(
    page_title="AI Chatbot powered by LlamaIndex",
    page_icon="🦙",
    layout="centered",
    initial_sidebar_state="auto",
    menu_items=None,
)
st.title("Create GenAI Chatbot")
st.info(
    "Use this page to train your chatbot agent on your data! "
    "To use the bot, select the 'Generated RAG Agent' menu.\n"
    "To build a new agent, select 'Create a new agent'.",
    icon="ℹ️",
)
if "metaphor_key" in st.secrets:
    st.info("**NOTE**: The ability to add web search is enabled.")


add_builder_config()
add_sidebar()

# Provide file upload option
doc_path = './cache/data/'
sidebar_placeholder = st.sidebar.container()
uploaded_file = st.file_uploader("Choose a file")
uploaded_file_prompt = ""

if uploaded_file is not None:
    doc_files = os.listdir(doc_path)
    for doc_file in doc_files:
        os.remove(doc_path + doc_file)

    bytes_data = uploaded_file.read()
    with open(f"{doc_path}{uploaded_file.name}", 'wb') as f: 
        f.write(bytes_data)

    SimpleDirectoryReader = download_loader("SimpleDirectoryReader")

    loader = SimpleDirectoryReader(doc_path, recursive=True, exclude_hidden=True)
    documents = loader.load_data()
    sidebar_placeholder.header('Current Processing Document:')
    sidebar_placeholder.subheader(uploaded_file.name)
    sidebar_placeholder.write(documents[0].get_text()[:10000]+'...')
    uploaded_file_prompt = f"The uploaded file name is ({doc_path}{uploaded_file.name})"

st.info(f"Currently building/editing chatbot: {current_state.cache.agent_id}", icon="ℹ️")

# add pills
selected = pills(
    "Outline your task!",
    [
        "I want to analyze this PDF file (data/invoices.pdf)",
        "I want to ask questions about this legal contract.",
        "I want to set the chunk size to 512 and retrieve 4 chunks at a time.",
    ],
    clearable=True,
    index=None,
)

if "messages" not in st.session_state.keys():  # Initialize the chat messages history
    st.session_state.messages = [
        {"role": "assistant", "content": "What type of chatbot would you like to build?"}
    ]


def add_to_message_history(role: str, content: str) -> None:
    message = {"role": role, "content": str(content)}
    st.session_state.messages.append(message)  # Add response to message history


for message in st.session_state.messages:  # Display the prior chat messages
    with st.chat_message(message["role"]):
        st.write(message["content"])

# TODO: this is really hacky, only because st.rerun is jank
if prompt := st.chat_input(
    "Your question",
):  # Prompt for user input and save to chat history
    # TODO: hacky
    if "has_rerun" in st.session_state.keys() and st.session_state.has_rerun:
        # if this is true, skip the user input
        st.session_state.has_rerun = False
    else:
        add_to_message_history("user", prompt)
        with st.chat_message("user"):
            st.write(prompt)

        # If last message is not from assistant, generate a new response
        if st.session_state.messages[-1]["role"] != "assistant":
            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    response = current_state.builder_agent.chat(uploaded_file_prompt + prompt)
                    st.write(str(response))
                    add_to_message_history("assistant", str(response))

        else:
            pass

        # check agent_ids again
        # if it doesn't match, add to directory and refresh
        agent_ids = current_state.agent_registry.get_agent_ids()
        # check diff between agent_ids and cur agent ids
        diff_ids = list(set(agent_ids) - set(st.session_state.cur_agent_ids))
        if len(diff_ids) > 0:
            # # clear streamlit cache, to allow you to generate a new agent
            # st.cache_resource.clear()
            st.session_state.has_rerun = True
            st.rerun()

else:
    # TODO: set has_rerun to False
    st.session_state.has_rerun = False
