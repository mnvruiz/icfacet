import streamlit as st
from google import genai
from google.genai import types
from google.genai.errors import APIError
from streamlit_geolocation import streamlit_geolocation
from geopy.geocoders import Nominatim

# 1. Configuración de la página
st.set_page_config(
    page_title="ChatBot IC-FACET",
    page_icon="💻",
    layout="centered"
)

st.title("💻 ChatBot Inteligencia Computacional - FACET")
st.markdown("""
### 🧠 Asistente diario
**Desarrollado por:** Lizárraga, Matteo y Ruiz  
*Modelo activo:* `gemini-3.5-flash`

""")

# 2. Barra de herramientas: GPS, Cámara y Micrófono
col_gps, col_cam, col_mic = st.columns([1, 1, 1])

# --- GPS ---
with col_gps:
    location = streamlit_geolocation()
    latitud = location.get("latitude") if location else None
    longitud = location.get("longitude") if location else None

# --- CÁMARA ---
with col_cam:
    with st.popover("📸 Sacar Foto"):
        foto_capturada = st.camera_input("Toma una foto para enviarla al bot")

# --- MICRÓFONO ---
with col_mic:
    with st.popover("🎙️ Dictado / Audio"):
        audio_grabado = st.audio_input("Graba una nota de voz")

# Traducir coordenadas a dirección real automáticamente
direccion_detectada = None
if latitud and longitud:
    try:
        geolocator = Nominatim(user_agent="icfacet_app")
        location_info = geolocator.reverse((latitud, longitud), timeout=5)
        if location_info:
            direccion_detectada = location_info.address
    except Exception:
        direccion_detectada = None

# Mensaje de estado
if direccion_detectada:
    st.success(f"📍 **Ubicación exacta:** {direccion_detectada}")
elif latitud and longitud:
    st.success(f"📍 **Ubicación GPS:** Lat {latitud:.4f}, Lon {longitud:.4f}")
else:
    st.info("💡 Puedes compartir tu **GPS (⌖)**, tomar una **Foto (📸)** o grabar **Audio (🎙️)** desde los botones superiores.")
    
# 3. Validación de API Key desde los Secrets de Streamlit
if "GEMINI_API_KEY" not in st.secrets or not st.secrets["GEMINI_API_KEY"]:
    st.error("⚠️ No se encontró la clave GEMINI_API_KEY en los Secrets de Streamlit. Por favor confígurala en los ajustes.")
    st.stop()

GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
client = genai.Client(api_key=GEMINI_API_KEY)
MODELO_NOMBRE = "gemini-3.5-flash"

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

# 6. Entrada del usuario (Texto o envío con multimedia)
prompt = st.chat_input("Escribe tu mensaje o consulta sobre la foto/audio...")

# Disparar envío si hay texto, foto o audio nuevo
if prompt or foto_capturada or audio_grabado:
    
    # Construcción de la parte multimedia del mensaje actual
    partes_usuario = []
    texto_a_mostrar = prompt if prompt else ""

    if foto_capturada:
        foto_bytes = foto_capturada.getvalue()
        partes_usuario.append(types.Part.from_bytes(data=foto_bytes, mime_type="image/jpeg"))
        texto_a_mostrar += "\n\n📷 *[Foto adjunta]*"

    if audio_grabado:
        audio_bytes = audio_grabado.getvalue()
        mime_type = audio_grabado.type if audio_grabado.type else "audio/wav"
        partes_usuario.append(types.Part.from_bytes(data=audio_bytes, mime_type=mime_type))
        texto_a_mostrar += "\n\n🎙️ *[Audio de voz adjunto]*"

    if prompt:
        partes_usuario.append(types.Part.from_text(text=prompt))
    elif not partes_usuario:
        # Si presionó enter sin texto ni archivos
        st.stop()

    # Si solo mandó audio/foto sin texto en la caja, poner un texto genérico para el historial
    if not texto_a_mostrar.strip():
        texto_a_mostrar = "Mira/Escucha este contenido multimedia."
        partes_usuario.append(types.Part.from_text(text=texto_a_mostrar))

    # Guardar y mostrar el mensaje del usuario
    st.session_state.messages.append({"role": "user", "content": texto_a_mostrar})
    with st.chat_message("user"):
        st.markdown(texto_a_mostrar)
        if foto_capturada:
            st.image(foto_capturada, width=300)
        if audio_grabado:
            st.audio(audio_grabado)

    # Armar historial para Gemini
    contents = []
    for msg in st.session_state.messages:
        role = "user" if msg["role"] == "user" else "model"
        contents.append(types.Content(
            role=role,
            parts=[types.Part.from_text(text=msg["content"])]
        ))
    
    # Reemplazar la última entrada con las partes reales que incluyen imágenes/audios en bytes
    contents[-1] = types.Content(role="user", parts=partes_usuario)

    # Inyectar GPS en las instrucciones
    system_instruction_actual = SYSTEM_INSTRUCTION_BASE
    if latitud and longitud:
        system_instruction_actual += f"\n\n[INFORMACIÓN DE CONTEXTO REAL: La ubicación GPS del usuario es Latitud {latitud}, Longitud {longitud}]."
    else:
        system_instruction_actual += "\n\n[INFORMACIÓN DE CONTEXTO: El usuario aún NO ha compartido su ubicación GPS]."

    config = types.GenerateContentConfig(
        system_instruction=system_instruction_actual,
        temperature=0.7
    )

    # Generación de la respuesta
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
        except APIError as e:
            st.error(f"⚠️ Error en los servidores de Google Gemini: {e.message}")
        except Exception as e:
            st.error(f"⚠️ Error al conectar con el asistente: {str(e)}")
