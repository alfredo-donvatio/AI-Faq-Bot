import streamlit as st

st.set_page_config(page_title="Demo RAG", page_icon="🤖")

st.title("🤖 Demo FAQs Bot con IA")

st.write("Haz una pregunta sobre las FAQs:")

query = st.text_input("Pregunta")

from agente import responder

if "historial" not in st.session_state:
    st.session_state.historial = []

if query:
    with st.spinner("Pensando..."):
        respuesta, st.session_state.historial = responder(query, st.session_state.historial)
    st.write(f"**Bot:** {respuesta}")