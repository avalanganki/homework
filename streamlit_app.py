import streamlit as st

st.set_page_config(
    page_title="488 Homework",
    page_icon="📌",
    layout="wide"
)

st.markdown('# 488 Homework')
st.markdown('## :red[Ava Langanki]')

p1 = st.Page('homework/hw1.py', title='Homework 1 - Document QA', icon='👩‍💻', default=False)
p2 = st.Page('homework/hw2.py', title='Homework 2 - URL Summarizer with Multiple LLMs', icon='💡', default=False)
p3 = st.Page('homework/hw3.py', title='Homework 3 - URL Summarizer with Conversation Memory', icon='💡', default=False)
p4 = st.Page('homework/hw4.py', title='Homework 4 - iSchool ChatBot Using RAG', icon='📊', default=False)
p5 = st.Page('homework/hw5.py', title='Homework 5 - Enhanced iSchool ChatBot', icon='📤', default=False)
p6 = st.Page('homework/hw7.py', title='Homework 7 - News ChatBot', icon='📤', default=True)

pg = st.navigation([p1, p2, p3, p4, p5, p6])

pg.run()
