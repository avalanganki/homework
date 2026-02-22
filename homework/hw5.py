import streamlit as st
from openai import OpenAI
__import__('pysqlite3')
import sys
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

import chromadb
from bs4 import BeautifulSoup
from pathlib import Path

chroma_client = chromadb.PersistentClient(path='./ChromaDB_HW5')
collection = chroma_client.get_or_create_collection('HW5_iSchool_Collection')

if 'openai_client' not in st.session_state:
    st.session_state.openai_client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

def extract_text_from_html(html_path):
    with open(html_path, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f.read(), 'html.parser')
        for script in soup(["script", "style"]):
            script.decompose()
        return soup.get_text()

def add_to_collection(collection, text, chunk_id, file_name):
    client = st.session_state.openai_client
    response = client.embeddings.create(input=text, model='text-embedding-3-small')
    embedding = response.data[0].embedding
    collection.add(
        documents=[text],
        ids=[chunk_id],
        embeddings=[embedding],
        metadatas=[{"filename": file_name}]
    )

def load_htmls_to_collection(folder_path, collection):
    if collection.count() == 0:
        for html_file in Path(folder_path).glob('*.html'):
            text = extract_text_from_html(str(html_file))
            mid = len(text) // 2
            add_to_collection(collection, text[:mid], f"{html_file.name}_1", html_file.name)
            add_to_collection(collection, text[mid:], f"{html_file.name}_2", html_file.name)

def relevant_club_info(query):
    query_emb = st.session_state.openai_client.embeddings.create(
        input=query, model='text-embedding-3-small'
    ).data[0].embedding
    
    results = collection.query(query_embeddings=[query_emb], n_results=5)
    
    context = ""
    for i in range(len(results['documents'][0])):
        context += f"\n{results['documents'][0][i][:1500]}"
    return context

st.title("HW5: Enhanced iSchool Chatbot")

if 'loaded' not in st.session_state:
    load_htmls_to_collection('./su_orgs/su_orgs/', collection)
    st.session_state.loaded = True

if 'messages' not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    st.chat_message(msg['role']).write(msg['content'])

if prompt := st.chat_input('Ask about student organizations...'):
    st.session_state.messages.append({'role': 'user', 'content': prompt})
    st.chat_message('user').write(prompt)
    
    club_info = relevant_club_info(prompt)
    
    system_msg = f"Answer using this info about student orgs:\n{club_info}"
    messages = [{"role": "system", "content": system_msg}] + st.session_state.messages[-10:]
    
    stream = st.session_state.openai_client.chat.completions.create(
        model='gpt-4o-mini',
        messages=messages,
        stream=True
    )
    
    with st.chat_message("assistant"):
        response = st.write_stream(stream)
    
    st.session_state.messages.append({'role': 'assistant', 'content': response})

st.sidebar.write(f"Documents: {collection.count()}")

if st.sidebar.button("Test Query"):
    test_info = relevant_club_info("student organizations")
    st.sidebar.write("Query returns:")
    st.sidebar.write(test_info[:500])  

if st.sidebar.button("Clear"):
    st.session_state.messages = []
    st.rerun()