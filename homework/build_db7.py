import sys
__import__('pysqlite3')
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

import chromadb
import pandas as pd
from openai import OpenAI
import streamlit as st

openai_client = OpenAI()
chroma_client = chromadb.PersistentClient(path="./Chroma_DB_HW7")


def load_and_clean_data(filepath="news.csv"):
    df = pd.read_csv(filepath)
    df = df.dropna(subset=["Document"]).reset_index(drop=True)
    return df


def get_or_create_collection(client, collection_name="news_collection"):
    try:
        client.delete_collection(collection_name)
    except Exception:
        pass
    return client.create_collection(
        name=collection_name,
        metadata={"hnsw:space": "cosine"}
    )


def add_to_collection(collection, text, chunk_id, metadata):
    response = openai_client.embeddings.create(
        input=text,
        model="text-embedding-3-small"
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

        if (idx + 1) % 50 == 0:
            print(f"Added {idx + 1} / {len(df)} articles")

    print(f"\nDone! {collection.count()} articles stored in ./chroma_db")

if __name__ == "__main__":
    df = load_and_clean_data()
    collection = get_or_create_collection(chroma_client)
    load_articles_to_collection(df, collection)