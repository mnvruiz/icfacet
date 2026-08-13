import streamlit as st
from google import genai
from google.genai import types
from google.genai.errors import APIError
from streamlit_geolocation import streamlit_geolocation

# 1. Configuración de la página
st.set_page_config(
    page_title="ChatBot IC-FACET",
    page_icon="💻",
    layout="centered"
)

st.title("💻 ChatBot Pensamiento Computacional - FACET")
st.markdown("""
### 🧠 Asistente diario
**Desarrollado por:** Matteo, Lizárraga y Ruiz  
*Modelo activo:* `gemini-3.6-flash`

""")

# 2. Captura de ubicación GPS en la barra lateral
st.sidebar.header("📍 Ubicación GPS")
st.sidebar.write("Haz clic para compartir tu ubicación:")
location = streamlit_geolocation()

latitud = location.get("latitude") if location else None
longitud = location.get("longitude") if location else None

if latitud and longitud:
    st.sidebar.success(f"Ubicación activa:\nLat: {latitud:.4f}, Lon: {longitud:.4f}")
else:
    st.sidebar.warning("Ubicación no compartida.")
    # Banner sugerente en la pantalla principal si aún no compartió la ubicación
    st.info("💡 **Sugerencia:** Si deseas respuestas basadas en tu ubicación, recuerda hacer clic en **'📍 Ubicación GPS'** en el menú lateral de la izquierda.")

# 3. Validación de API Key desde los Secrets de Streamlit
if "GEMINI_API_KEY" not in st.secrets or not st.secrets["GEMINI_API_KEY"]:
    st.error("⚠️ No se encontró la clave GEMINI_API_KEY en los Secrets de Streamlit. Por favor confígurala en los ajustes.")
    st.stop()

GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
client = genai.Client(api_key=GEMINI_API_KEY)
MODELO_NOMBRE = "gemini-2.5-flash"

# 4. Instrucción del Sistema Base
SYSTEM_INSTRUCTION_BASE = """
Eres un asistente conversacional reflexivo especializado en Inteligencia Computacional y soporte intrapersonal.
Proceso de NLU: Analiza implícitamente la emoción, la intención y los conceptos clave del usuario en cada mensaje.

Instrucciones de comportamiento:
1. Ayuda al usuario a descomponer problemas complejos, reconocer patrones, abstraer ideas y diseñar algoritmos de solución.
2. Actúa como un espejo reflexivo: mantén un tono empático, analítico y constructivo.
3. Haz preguntas abiertas que inviten a la introspección antes de dar conclusiones apresuradas.
4. BREVEDAD: Intenta responder de forma concisa y directa para favorecer la fluidez, pero asegúrate de desarrollar la idea completa sin cortar información.
5. UBICACIÓN: Si el usuario te consulta algo que requiere saber dónde se encuentra y NO tienes sus coordenadas en el contexto, pídele amablemente que haga clic en el botón '📍 Ubicación GPS' situado en la barra lateral izquierda.
"""

# 5. Inicialización del historial de chat en la sesión
if "messages" not in st.session_state:
    st.session_state.messages = []

# Mostrar mensajes previos del historial
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 6. Entrada del usuario y generación de respuesta
if prompt := st.chat_input("Escribe tu mensaje..."):
    # Guardar y mostrar el mensaje del usuario
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Reconstruir el historial con tipos explícitos de Content
    contents = []
    for msg in st.session_state.messages:
        role = "user" if msg["role"] == "user" else "model"
        contents.append(types.Content(
            role=role,
            parts=[types.Part.from_text(text=msg["content"])]
        ))

    # Incorporar información de ubicación en la instrucción si está activa
    system_instruction_actual = SYSTEM_INSTRUCTION_BASE
    if latitud and longitud:
        system_instruction_actual += f"\n\n[INFORMACIÓN DE CONTEXTO REAL: La ubicación GPS del usuario es Latitud {latitud}, Longitud {longitud}]."
    else:
        system_instruction_actual += "\n\n[INFORMACIÓN DE CONTEXTO: El usuario aún NO ha compartido su ubicación GPS]."

    config = types.GenerateContentConfig(
        system_instruction=system_instruction_actual,
        temperature=0.7
    )

    # Respuesta en streaming con manejo de errores
    with st.chat_message("assistant"):
        try:
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

        except APIError as e:
            st.error(f"⚠️ Error en los servidores de Google Gemini: {e.message}")
        except Exception as e:
            st.error(f"⚠️ Error al conectar con el asistente: {str(e)}")
