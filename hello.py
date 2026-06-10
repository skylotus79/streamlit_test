import streamlit as st

st.title("Hello Streamlit!")
st.write("Welcome to your first Streamlit app")

name = st.text_input("What's your name?")
if name:
    st.write(f"Hello, {name}!")
