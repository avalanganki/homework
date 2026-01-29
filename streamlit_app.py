import streamlit as st

st.set_page_config(
    page_title="488 Homework",
    page_icon="🔬",
    layout="wide"
)

st.markdown('# 488 Homework')
st.markdown('## :red[Ava Langanki]')

p1 = st.Page('homework/hw1.py', title='Homework 1 - Document QA', icon='👩‍💻', default=False)
p2 = st.Page('homework/hw2.py', title='Homework 2 - URL Summarizer with Multiple LLMs', icon='💡', default=True)

pg = st.navigation([p1, p2])

pg.run()
