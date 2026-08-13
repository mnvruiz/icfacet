import streamlit as st
from google import genai
from google.genai import types

# 1. Configuración de la página
st.set_page_config(
    page_title="ChatBot Pensamiento Computacional - FACET",
    page_icon="💻",
    layout="centered"
)

st.title("💻 ChatBot Pensamiento Computacional - FACET")
st.markdown("""
### 🧠 Asistente Conversacional e Intrapersonal
**Desarrollado por:** Matteo, Lizárraga y Ruiz  
*Modelo activo:* `gemini-1.5-flash`

---
*Espacio diseñado para descomponer problemas complejos, organizar ideas y fomentar la introspección.*
""")

# 2. Validación de API Key desde los Secrets de Streamlit
if "GEMINI_API_KEY" not in st.secrets:
    st.error("⚠️ No se encontró la clave GEMINI_API_KEY en los Secrets de Streamlit. Por favor confígurala en los ajustes.")
    st.stop()

GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
client = genai.Client(api_key=GEMINI_API_KEY)
MODELO_NOMBRE = "gemini-1.5-flash"

# 3. Instrucción del Sistema
SYSTEM_INSTRUCTION = """
Eres un asistente conversacional reflexivo especializado en Pensamiento Computacional y soporte intrapersonal.
Proceso de NLU: Analiza implícitamente la emoción, la intención y los conceptos clave del usuario en cada mensaje.

Instrucciones de comportamiento:
1. Ayuda al usuario a descomponer problemas complejos, reconocer patrones, abstraer ideas y diseñar algoritmos de solución.
2. Actúa como un espejo reflexivo: mantén un tono empático, analítico y constructivo.
3. Haz preguntas abiertas que inviten a la introspección antes de dar conclusiones apresuradas.
4. BREVEDAD: Intenta responder de forma concisa y directa para favorecer la fluidez, pero asegúrate de desarrollar la idea completa sin cortar información.
"""

# 4. Inicialización del historial de chat
if "messages" not in st.session_state:
    st.session_state.messages = []

# Mostrar mensajes anteriores
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 5. Interacción del usuario y respuesta en streaming
if prompt := st.chat_input("Escribe tu mensaje..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    contents = []
    for msg in st.session_state.messages:
        role = "user" if msg["role"] == "user" else "model"
        contents.append({"role": role, "parts": [{"text": msg["content"]}]})

    config = types.GenerateContentConfig(
        system_instruction=SYSTEM_INSTRUCTION,
        temperature=0.7
    )

    with st.chat_message("assistant"):
        def response_generator():
            response_stream = client.models.generate_content_stream(
                model=MODELO_NOMBRE,
                contents=contents,
                config=config
            )
            for chunk in response_stream:
                if chunk.text:
                    yield chunk.text

        full_response = st.write_stream(response_generator())

    st.session_state.messages.append({"role": "assistant", "content": full_response})
