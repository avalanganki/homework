__import__('pysqlite3')
import sys
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

import streamlit as st
from openai import OpenAI
import chromadb
import pandas as pd
import os

if 'openai_client' not in st.session_state:
    st.session_state.openai_client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

@st.cache_resource
def build_collection():
    client = chromadb.Client()
    col = client.get_or_create_collection("news_collection")

    openai_client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

    csv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "news.csv")
    df = pd.read_csv(csv_path)
    df = df.dropna(subset=["Document"]).reset_index(drop=True)

    batch_size = 50
    for i in range(0, len(df), batch_size):
        batch = df.iloc[i:i + batch_size]
        texts = batch["Document"].tolist()
        ids = [f"article_{idx}" for idx in batch.index]
        metadatas = [
            {
                "company_name": str(row["company_name"]),
                "date": str(row["Date"]),
                "url": str(row["URL"]),
                "days_since_2000": int(row["days_since_2000"])
            }
            for _, row in batch.iterrows()
        ]

        response = openai_client.embeddings.create(
            input=texts, model="text-embedding-3-small"
        )
        embeddings = [item.embedding for item in response.data]

        col.add(
            documents=texts,
            ids=ids,
            embeddings=embeddings,
            metadatas=metadatas
        )

    return col

with st.spinner("Loading articles..."):
    collection = build_collection()

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

st.title("HW7: News Bot")

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