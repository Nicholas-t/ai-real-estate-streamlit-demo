from openai import OpenAI
import streamlit as st
import time
import re

import pandas as pd


CITY_FILE_MAPPING = pd.read_csv("./city_file_mapping.csv").to_dict(orient="records")

def add_chat_to_ui(role, content):
    cm = None
    if role== "assistant":
        cm = st.chat_message(role, avatar="https://d2kity9bboyw3j.cloudfront.net/assets/images/brand/sf_favicon-7eaf1130.png")
    else:
        cm = st.chat_message(role)
    with cm:
        content_splitted = content.split("\n")
        for each_line in content_splitted:
            st.write(each_line)
    
def add_new_message(role, content):
    add_chat_to_ui(role, content)
    st.session_state.messages.append({"role": role, "content": content})

def add_user_response_and_wait_openai(client, thread_id, content="", file_ids=[], max_attempt = 200):
    client.beta.threads.messages.create(
        thread_id=thread_id,
        role="user",
        file_ids=file_ids,
        content= content
    )
    run = client.beta.threads.runs.create(
        thread_id=thread_id,
        assistant_id="asst_mSAuJXucyEGL62iPZ3lKQzAJ"
    )

    last_status = "in_progress"
    while last_status != "completed" and max_attempt > 0:
        print("waiting")
        time.sleep(2)
        check = client.beta.threads.runs.retrieve(
            thread_id=thread_id,
            run_id=run.id
        )
        last_status = check.status
        max_attempt -= 1
    if last_status == "completed":
        messages = client.beta.threads.messages.list(
            thread_id=thread_id
        )
        response = messages.data[0].content[0].text.value
        response = re.sub(r"【.*?】", '', response)
        return response
    else:
        print("last_status : {}".format(last_status))
        print(check)
        return "ERROR"
    
def launch_assistant(city):
    file_id = ""
    for f in CITY_FILE_MAPPING:
        if f["city_slug"] == city:
            file_id = f["file_id"]
    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
    st.title("🤖💬 Storefront AI Helper") 
    
    if "messages" not in st.session_state:
        thread = client.beta.threads.create()
        st.session_state["thread_id"] = thread.id
        st.session_state["messages"] = []
        add_new_message("assistant", "Welcome to Storefront - {}! Tell me more about your project and I can suggest you spaces that could be interesting".format(city))
    else:
        for msg in st.session_state.messages:
            add_chat_to_ui(msg["role"], msg["content"])
    if prompt := st.chat_input():
        add_new_message("user", prompt)
        response = add_user_response_and_wait_openai(client, st.session_state["thread_id"], prompt, file_ids=[file_id])
        add_new_message("assistant", response)
    
hide_toolbar_css = """
<style>
[data-testid='stToolbar'] {
    display:none;
}

footer {
    visibility: hidden;
}
.css-1y4p8pa {
    padding-top: 1rem;
} 
</style>
"""
st.markdown(hide_toolbar_css, unsafe_allow_html=True)

city_input = ""
with st.sidebar:
    city_input = st.selectbox("City to test", key="city", options=[a["city_slug"] for a in CITY_FILE_MAPPING])

if "city" in st.session_state:
    if city_input != st.session_state["city"]:
        print("RESETTING MESSAGES AND THREADS")
        del st.session_state["messages"]
        del st.session_state["thread_id"]
else:
    st.session_state["city"] = city_input

launch_assistant(city_input)

#Hi I am looking to host an event in Los Angeles, my budget is 3k per day max