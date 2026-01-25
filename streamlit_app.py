import streamlit as st

st.set_page_config(
    page_title="488 Homework",
    page_icon="🔬",
    layout="wide"
)

st.markdown('# 488 Homework')
st.markdown('## :red[Ava Langanki]')

p1 = st.Page('homework/hw1.py', title='Homework 1 - Document QA', icon='👩‍💻', default=False)

pg = st.navigation([p1])

pg.run()
