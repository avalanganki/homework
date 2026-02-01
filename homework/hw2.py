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
        print(f"Error reading {url}: (e)")
        return None
    
st.title("Document QA For URL")
secret_key = st.secrets['OPENAI_API_KEY']
key_two = st.secrets['ANTHROPIC_KEY']

model = st.sidebar.selectbox('Which LLM:', ['OpenAI', 'Claude'])

options = st.sidebar.selectbox('Choose language:',
    ('English', 'Spanish', 'Italian'))

if options == 'English':
    prompt_instructions = "Summarize in English"
elif options == 'Spanish':
    prompt_instructions = "Summarize in Spanish"
else:
    prompt_instructions = "Summarize in italian"

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

st.sidebar.write("Using model: {selected_model}")

url_input = st.text_input("Enter URL:", placeholder="https://example.com")

if st.button("Summarize") and url_input: 
    document = read_url_content(url_input)
    if document:
            with st.spinner("Generating summary..."):
                if model == 'OpenAI':
                    if not secret_key:
                        st.error("OpenAI API key not found")
                    else:
                        client = OpenAI(api_key=secret_key)
                        messages = [
                            {
                                "role": "user",
                                "content": f"{prompt_instructions}:\n\n{document}",
                            }
                        ]
                        
                        stream = client.chat.completions.create(
                            model=selected_model,
                            messages=messages,
                            stream=True,
                        )
                        
                        st.write_stream(stream)
                
                elif model == 'Claude':
                    if not key_two:
                        st.error("Anthropic API key not found")
                    else:
                        client = Anthropic(api_key=key_two)
                        
                        with client.messages.stream(
                            model=selected_model,
                            max_tokens=2048,
                            messages=[
                                {
                                    "role": "user",
                                    "content": f"{prompt_instructions}:\n\n{document}",
                                }
                            ],
                        ) as stream:
                            st.write_stream(stream.text_stream)
    else:
        st.error("Failed to fetch content from URL")

    # to do 
    # secret ai key DONE
    # read url instead of pdf/txt
    # dropdown menu for language DONE
    # sidebar option to choose between two llms (openai and claude)
    # 'advanced' model button DONE
