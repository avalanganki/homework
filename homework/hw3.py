import streamlit as st
from openai import OpenAI
from anthropic import Anthropic
import requests
from bs4 import BeautifulSoup

def read_url_content(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        return soup.get_text()
    except requests.RequestException as e:
        print(f"Error reading {url}: {e}")
        return None

st.title("HW3: URL Discussion Chatbot")
st.write("**Memory:** 6-message buffer (3 exchanges). URL content stays in system prompt.")

secret_key = st.secrets.get('OPENAI_API_KEY')
key_two = st.secrets.get('ANTHROPIC_KEY')

model = st.sidebar.selectbox('Which LLM:', ['OpenAI', 'Claude'])

use_advanced_model = st.sidebar.checkbox('Use Advanced Model')
if model == 'OpenAI':
    if use_advanced_model:
        selected_model = 'gpt-4o'
    else:
        selected_model = 'gpt-4o-mini'
elif model == 'Claude':
    if use_advanced_model:
        selected_model = 'claude-opus-4-20250514'
    else:
        selected_model = 'claude-sonnet-4-20250514'

st.sidebar.write(f"Using model: {selected_model}")

url1 = st.sidebar.text_input("URL 1:", placeholder="https://example.com")
url2 = st.sidebar.text_input("URL 2 (optional):", placeholder="https://example.com")

if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'url_context' not in st.session_state:
    st.session_state.url_context = ""

if st.sidebar.button("Load URLs") and url1:
    url_context = ""
    
    document1 = read_url_content(url1)
    if document1:
        url_context += f"\n\n=== URL 1 ===\n{document1[:3000]}"
    
    if url2:
        document2 = read_url_content(url2)
        if document2:
            url_context += f"\n\n=== URL 2 ===\n{document2[:3000]}"
    
    if url_context:
        st.session_state.url_context = url_context
        st.sidebar.success("URLs loaded!")
    else:
        st.sidebar.error("Failed to fetch content from URLs")

for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

if prompt := st.chat_input("Ask about the URLs..."):
    st.session_state.messages.append({'role': 'user', 'content': prompt})
    with st.chat_message('user'):
        st.markdown(prompt)
    
    system_prompt = f"Use this content to answer:\n{st.session_state.url_context}\n\nIf not in content, say so."
    
    recent_messages = st.session_state.messages[-6:]
    
    with st.spinner("Generating response..."):
        if model == 'OpenAI':
            if not secret_key:
                st.error("OpenAI API key not found")
            else:
                client = OpenAI(api_key=secret_key)
                messages = [{"role": "system", "content": system_prompt}] + recent_messages
                
                stream = client.chat.completions.create(
                    model=selected_model,
                    messages=messages,
                    stream=True,
                )
                
                with st.chat_message("assistant"):
                    response = st.write_stream(stream)
        
        elif model == 'Claude':
            if not key_two:
                st.error("Anthropic API key not found")
            else:
                client = Anthropic(api_key=key_two)
                
                with client.messages.stream(
                    model=selected_model,
                    max_tokens=2048,
                    system=system_prompt,
                    messages=recent_messages,
                ) as stream:
                    with st.chat_message("assistant"):
                        response = st.write_stream(stream.text_stream)
    
    st.session_state.messages.append({'role': 'assistant', 'content': response})

if st.sidebar.button("Clear Chat"):
    st.session_state.messages = []
    st.rerun()