import streamlit as st
from openai import OpenAI
# Source - https://stackoverflow.com/a/78237141
# Posted by pintz
# Retrieved 2026-02-11, License - CC BY-SA 4.0
__import__('pysqlite3')
import sys
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

import chromadb
from bs4 import BeautifulSoup
from pathlib import Path

chroma_client = chromadb.PersistentClient(path='./ChromaDB_HW4')
collection = chroma_client.get_or_create_collection('HW4_iSchool_Collection')

if 'openai_client' not in st.session_state:
    st.session_state.openai_client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

def extract_text_from_html(html_path):
    """Extract text from HTML file"""
    with open(html_path, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f.read(), 'html.parser')
        for script in soup(["script", "style"]):
            script.decompose()
        return soup.get_text()

def chunk_document(text, filename):
    mid = len(text) // 2
    chunk1 = text[:mid].strip()
    chunk2 = text[mid:].strip()
    return [(chunk1, f"{filename}_part1"), (chunk2, f"{filename}_part2")]

def load_htmls_to_collection(folder_path, collection):
    if collection.count() == 0:
        html_files = Path(folder_path).glob('*.html')
        for html_file in html_files:
            text = extract_text_from_html(str(html_file))
            chunks = chunk_document(text, html_file.name)
            
            for chunk_text, chunk_id in chunks:
                add_to_collection(collection, chunk_text, chunk_id, html_file.name)
        return True
    return False

def add_to_collection(collection, text, chunk_id, file_name):
    client = st.session_state.openai_client
    response = client.embeddings.create(
        input=text,
        model='text-embedding-3-small'
    )
    embedding = response.data[0].embedding
    collection.add(
        documents=[text],
        ids=[chunk_id],
        embeddings=[embedding],
        metadatas=[{"filename": file_name, "chunk_id": chunk_id}]
    )
    
st.title("HW4: iSchool ChatBot Using RAG")

if 'hw4_messages' not in st.session_state:
    st.session_state.hw4_messages = []

for msg in st.session_state.hw4_messages:
    st.chat_message(msg['role']).write(msg['content'])

if prompt := st.chat_input('Ask about iSchool student organizations...'):
    st.session_state.hw4_messages.append({'role': 'user', 'content': prompt})
    st.chat_message('user').write(prompt)

    query_response = st.session_state.openai_client.embeddings.create(
        input=prompt,
        model='text-embedding-3-small'
    )
    query_embedding = query_response.data[0].embedding

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=3
    )

    context = ""
    for i in range(len(results['documents'][0])):
        filename = results['metadatas'][0][i]['filename']
        doc_text = results['documents'][0][i][:800]
        context += f"\n\nFrom {filename}:\n{doc_text}"
    
    system_prompt = f"You help answer questions about iSchool student organizations. Use this info:\n{context}"
    
    # Keep last 5 interactions (10 messages total)
    recent_messages = st.session_state.hw4_messages[-10:]
    messages = [{"role": "system", "content": system_prompt}] + recent_messages
    
    client = st.session_state.openai_client
    stream = client.chat.completions.create(
        model='gpt-4o-mini',
        messages=messages,
        stream=True
    )
    
    with st.chat_message("assistant"):
        response = st.write_stream(stream)
    
    st.session_state.hw4_messages.append({'role': 'assistant', 'content': response})

st.sidebar.write(f"Buffer: {min(10, len(st.session_state.hw4_messages))}/10 messages")

if st.sidebar.button("Clear"):
    st.session_state.hw4_messages = []
    st.rerun()