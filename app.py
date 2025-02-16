import streamlit as st
from streamlit_chat import message
import dotenv
import os
import openai
import datetime
import json
import logging

# adjust as needed
logging.basicConfig(level=logging.INFO)

# Load environment variables
ENV = dotenv.dotenv_values(".env")

# Set up the Open AI Client
openai.api_type = ENV["API_TYPE"]
if ENV["API_TYPE"] == "azure":
    openai.api_base = ENV["AZURE_OPENAI_ENDPOINT"]
    openai.api_version = ENV["AZURE_OPENAI_API_VERSION"]
    openai.api_key = ENV["AZURE_OPENAI_KEY"]
else:
    openai.api_key = ENV["OPENAI_API_KEY"]

# generates responses to prompts
def generate_response(prompt, temperature, topp):
    st.session_state["messages"].append({"role": "user", "content": prompt})
    completion, response = None, None
    try:
        if ENV["API_TYPE"] == "azure":
            completion = openai.ChatCompletion.create(
                engine=ENV["AZURE_OPENAI_CHATGPT_DEPLOYMENT"],
                messages=st.session_state["messages"],
                temperature=temperature,
                top_p=topp,
            )
        else:
            completion = openai.ChatCompletion.create(
                model=ENV["OPENAI_MODEL"],
                messages=st.session_state["messages"],
                temperature=temperature,
                top_p=topp,
            )
        response = completion.choices[0].message.content
    except Exception as e:
        st.write(response)
        response = f"The API could not handle this content: {str(e)}"
    st.session_state["messages"].append({"role": "assistant", "content": response})

    return (
        response,
        completion.usage.total_tokens,
        completion.usage.prompt_tokens,
        completion.usage.completion_tokens,
    )


# PROMPT SETUP
default_prompt = """
You are a helpful assistant. Provide all answers in markdown format.
"""

seed_message = {"role": "system", "content": default_prompt}

st.set_page_config(page_title="Nearly ChatGPT", page_icon=":mountain:", layout="wide")
st.title("Nearly ChatGPT")

# SESSION MANAGEMENT
# Initialise session state variables
if "generated" not in st.session_state:
    st.session_state["generated"] = []
if "past" not in st.session_state:
    st.session_state["past"] = []
if "messages" not in st.session_state:
    st.session_state["messages"] = [seed_message]
if "model_name" not in st.session_state:
    st.session_state["model_name"] = []
if "cost" not in st.session_state:
    st.session_state["cost"] = []
if "total_tokens" not in st.session_state:
    st.session_state["total_tokens"] = []
if "prompt_tokens" not in st.session_state:
    st.session_state["prompt_tokens"] = []
if "completion_tokens" not in st.session_state:
    st.session_state["completion_tokens"] = []
if "total_cost" not in st.session_state:
    st.session_state["total_cost"] = 0.0
if "prompt_cost" not in st.session_state:
    st.session_state["prompt_cost"] = 0.0
if "completion_cost" not in st.session_state:
    st.session_state["completion_cost"] = 0.0
if "temperature" not in st.session_state:
    st.session_state["temperature"] = 1.0
if "topp" not in st.session_state:
    st.session_state["topp"] = 1.0

# SIDEBAR SETUP
st.sidebar.write("Total cost of this conversation")
total_cost_placeholder = st.sidebar.empty()
total_cost_placeholder.code(f"${st.session_state['total_cost']:.5f}")
st.sidebar.write("Total cost of prompts")
prompt_cost_placeholder = st.sidebar.empty()
prompt_cost_placeholder.code(f"${st.session_state['prompt_cost']:.5f}")
st.sidebar.write("Total cost of completions")
completion_cost_placeholder = st.sidebar.empty()
completion_cost_placeholder.code(f"${st.session_state['completion_cost']:.5f}")
temperature = st.sidebar.slider(
    "Temperature", 0.0, 1.0, st.session_state["temperature"]
)
topp = st.sidebar.slider("Top P", 0.0, 1.0, st.session_state["topp"])
clear_button = st.sidebar.button("Clear Conversation", key="clear")

if clear_button:
    st.session_state["generated"] = []
    st.session_state["past"] = []
    st.session_state["messages"] = [seed_message]
    st.session_state["number_tokens"] = []
    st.session_state["model_name"] = []
    st.session_state["cost"] = []
    st.session_state["total_cost"] = 0.0
    st.session_state["total_tokens"] = []
    st.session_state["prompt_tokens"] = []
    st.session_state["completion_tokens"] = []
    total_cost_placeholder.code(f"${st.session_state['total_cost']:.5f}")
    prompt_cost_placeholder.code(f"${st.session_state['prompt_cost']:.5f}")
    completion_cost_placeholder.code(f"${st.session_state['completion_cost']:.5f}")
    

download_conversation_button = st.sidebar.download_button(
    "Download Conversation",
    data=json.dumps(st.session_state["messages"]),
    file_name="conversation.json",
    mime="text/json",
)

# container for chat history
response_container = st.container()

# container for text box
container = st.container()

with container:
    with st.form(key="my_form", clear_on_submit=True):
        user_input = st.text_area("You:", key="input", height=100)
        submit_button = st.form_submit_button(label="Send")

    with st.spinner("Talking with AI..."):
        if submit_button and user_input:
            output, total_tokens, prompt_tokens, completion_tokens = generate_response(
                user_input, temperature, topp
            )
            st.session_state["past"].append(user_input)
            st.session_state["generated"].append(output)
            if ENV["API_TYPE"] == "azure":
                st.session_state["model_name"].append(
                    ENV["AZURE_OPENAI_CHATGPT_DEPLOYMENT"]
                )
            else:
                st.session_state["model_name"].append(ENV["OPENAI_MODEL"])
            st.session_state["total_tokens"].append(total_tokens)
            st.session_state["prompt_tokens"].append(prompt_tokens)
            st.session_state["completion_tokens"].append(completion_tokens)

            cost = prompt_tokens * float(ENV["COST_PROMPT"]) / 1000 + completion_tokens * float(ENV["COST_COMPLETION"]) / 1000

            st.session_state["cost"].append(cost)
            st.session_state["total_cost"] += cost
            
            st.session_state["prompt_cost"] += prompt_tokens * float(ENV["COST_PROMPT"]) / 1000
            st.session_state["completion_cost"] += completion_tokens * float(ENV["COST_COMPLETION"]) / 1000

if st.session_state["generated"]:
    with response_container:
        for i in range(len(st.session_state["generated"])):
            message(
                st.session_state["past"][i],
                is_user=True,
                key=str(i) + "_user",
            )
            message(st.session_state["generated"][i], key=str(i))
        total_cost_placeholder.code(f"${st.session_state['total_cost']:.5f}")
        prompt_cost_placeholder.code(f"${st.session_state['prompt_cost']:.5f}")
        completion_cost_placeholder.code(f"${st.session_state['completion_cost']:.5f}")
