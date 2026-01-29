import streamlit as st
from openai import OpenAI
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
secret_key = st.secrets.OPENAI_API_KEY
client = OpenAI(api_key=secret_key)

st.sidebar.title("Language Menu")
options = st.sidebar.selectbox('Choose language:',
    ('English', 'Spanish', 'Italian'))

if options == 'English':
    prompt_instructions = "Summarize in English"
elif options == 'Spanish':
    prompt_instructions = "Summarize in Spanish"
else:
    prompt_instructions = "Summarize in italian"

use_advanced_model = st.sidebar.checkbox('Use Advanced Model')

if use_advanced_model:
    model_to_use = 'gpt-4o'  
else:
    model_to_use = 'gpt-4o-mini' 
st.sidebar.write("Using model: {model_to_use}")

selected_model = "gpt-3.5-turbo" ##OPENAI OR CLAUDE -- FIND INSTRUCTIONS

uploaded_file = st.file_uploader(
    "Paste a URL", type=()
    )

if uploaded_file and options: 
    document = uploaded_file.read()
    messages = [
        {
            "role": "user",
            "content": f"{prompt_instructions}\n\nDocument: {document}",
        }
    ]

if selected_model == 'OpenAI':
    model_to_use = 'gpt-3.5-turbo'
elif selected_model == 'Claude':
    model_to_use = 'claude-sonnet-4-20250514'
    # where API choices happen model = selected model 
        
    stream = client.chat.completions.create(
        model=model_to_use,
        messages=messages,
        stream=True,
    )

    st.write_stream(stream)
    
    # to do 
    # secret ai key DONE
    # read url instead of pdf/txt
    # dropdown menu for language DONE
    # sidebar option to choose between two llms (openai and claude)
    # 'advanced' model button DONE
