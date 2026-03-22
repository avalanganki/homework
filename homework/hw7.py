__import__('pysqlite3')
import sys
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

import streamlit as st
from openai import OpenAI
import chromadb
import pandas as pd

chroma_client = chromadb.PersistentClient(path="./Chroma_DB_HW7")
collection = chroma_client.get_or_create_collection("news_collection")

if 'openai_client' not in st.session_state:
    st.session_state.openai_client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

def add_to_collection(collection, text, chunk_id, metadata):
    response = st.session_state.openai_client.embeddings.create(
        input=text, model="text-embedding-3-small"
    )
    embedding = response.data[0].embedding
    collection.add(
        documents=[text],
        ids=[chunk_id],
        embeddings=[embedding],
        metadatas=[metadata]
    )


def load_articles_to_collection(df, collection):
    for idx, row in df.iterrows():
        metadata = {
            "company_name": str(row["company_name"]),
            "date": str(row["Date"]),
            "url": str(row["URL"]),
            "days_since_2000": int(row["days_since_2000"])
        }
        add_to_collection(
            collection,
            text=row["Document"],
            chunk_id=f"article_{idx}",
            metadata=metadata
        )


if collection.count() == 0:
    with st.spinner("Building article database..."):
        df = pd.read_csv("news.csv")
        df = df.dropna(subset=["Document"]).reset_index(drop=True)
        load_articles_to_collection(df, collection)

def get_relevant_articles(query, n_results=10):
    query_emb = st.session_state.openai_client.embeddings.create(
        input=query, model="text-embedding-3-small"
    ).data[0].embedding

    results = collection.query(query_embeddings=[query_emb], n_results=n_results)

    context = ""
    for i in range(len(results["documents"][0])):
        meta = results["metadatas"][0][i]
        context += (
            f"\n[Article {i + 1}]\n"
            f"Company: {meta['company_name']}\n"
            f"Date: {meta['date']}\n"
            f"URL: {meta['url']}\n"
            f"Content: {results['documents'][0][i][:2000]}\n"
            f"---"
        )
    return context


SYSTEM_PROMPT = """You are a news assistant for a global law firm. Only use articles from the provided context. Never make up articles.
For "most interesting news": rank by legal/business significance (lawsuits, deals, regulatory actions, executive changes). Return a numbered list with company, date, summary, why it matters, and URL.
For topic/company questions: summarize the most relevant articles with company, date, and URL.
Be concise and professional."""

st.title("HW7: News Intelligence Bot")

if 'messages' not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    st.chat_message(msg['role']).write(msg['content'])

model_choice = st.sidebar.radio(
    "Select LLM",
    ["gpt-4o", "gpt-4o-mini"],
)

st.sidebar.write(f"Articles loaded: {collection.count()}")

if st.sidebar.button("Test Query"):
    test_info = get_relevant_articles("interesting news")
    st.sidebar.write("Query returns:")
    st.sidebar.write(test_info[:500])

if st.sidebar.button("Clear"):
    st.session_state.messages = []
    st.rerun()

if prompt := st.chat_input("Ask about the news..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)

    article_context = get_relevant_articles(prompt)

    system_msg = f"{SYSTEM_PROMPT}\n\nHere are the relevant news articles:\n{article_context}"
    messages = [{"role": "system", "content": system_msg}] + st.session_state.messages[-10:]

    stream = st.session_state.openai_client.chat.completions.create(
        model=model_choice,
        messages=messages,
        stream=True,
        temperature=0.3
    )

    with st.chat_message("assistant"):
        response = st.write_stream(stream)

    st.session_state.messages.append({"role": "assistant", "content": response})