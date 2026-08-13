<!DOCTYPE html>
<html>
<head>
  <script type="module" src="https://cdn.jsdelivr.net/npm/@gradio/lite"></script>
  <style>
    body { 
      margin: 0; 
      padding: 0; 
      background-color: #f8f9fa;
    }
  </style>
</head>
<body>
  <gradio-lite>
    <!-- Declaración de librerías Python necesarias para la ejecución client-side -->
    <gradio-requirements>
google-genai
    </gradio-requirements>

    <gradio-file name="app.py">
import os
import gradio as gr
from google import genai
from google.genai import types

# 1. Configuración de la API Key (Pega tu clave aquí)
GEMINI_API_KEY = ""

# Inicialización del cliente
client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None
MODELO_NOMBRE = "gemini-1.5-flash"

# 2. Instrucción del Sistema
SYSTEM_INSTRUCTION = """
Eres un asistente conversacional reflexivo especializado en Pensamiento Computacional y soporte intrapersonal.
Proceso de NLU: Analiza implícitamente la emoción, la intención y los conceptos clave del usuario en cada mensaje.

Instrucciones de comportamiento:
1. Ayuda al usuario a descomponer problemas complejos, reconocer patrones, abstraer ideas y diseñar algoritmos de solución.
2. Actúa como un espejo reflexivo: mantén un tono empático, analítico y constructivo.
3. Haz preguntas abiertas que inviten a la introspección antes de dar conclusiones apresuradas.
4. BREVEDAD: Intenta responder de forma concisa y directa para favorecer la fluidez, pero asegúrate de desarrollar la idea completa sin cortar información.
"""

def responder(mensaje, historial):
    if not GEMINI_API_KEY:
        yield "⚠️ Por favor, ingresa tu GEMINI_API_KEY en la variable del código `app.py`."
        return

    try:
        contents = []

        # Reconstruir el historial de mensajes
        for item in historial:
            if isinstance(item, dict):
                role = "user" if item.get("role") == "user" else "model"
                texto = item.get("content", "")
                if texto:
                    contents.append({"role": role, "parts": [{"text": str(texto)}]})
            elif isinstance(item, (list, tuple)) and len(item) == 2:
                u_msg, b_msg = item[0], item[1]
                if u_msg:
                    contents.append({"role": "user", "parts": [{"text": str(u_msg)}]})
                if b_msg:
                    contents.append({"role": "model", "parts": [{"text": str(b_msg)}]})

        contents.append({"role": "user", "parts": [{"text": str(mensaje)}]})

        # Configuración de generación
        config = types.GenerateContentConfig(
            system_instruction=SYSTEM_INSTRUCTION,
            temperature=0.7
        )

        # Generación por streaming
        response_stream = client.models.generate_content_stream(
            model=MODELO_NOMBRE,
            contents=contents,
            config=config
        )

        texto_acumulado = ""
        for chunk in response_stream:
            if chunk.text:
                texto_acumulado += chunk.text
                yield texto_acumulado

    except Exception as e:
        yield f"⚠️ Error en la conversación: {str(e)}"

# 3. Interfaz de Gradio
demo = gr.ChatInterface(
    fn=responder,
    title="💻 ChatBot Pensamiento Computacional - FACET",
    description=f"""
    ### 🧠 Asistente Conversacional e Intrapersonal
    **Desarrollado por:** Matteo, Lizárraga y Ruiz  
    *Modelo activo:* `{MODELO_NOMBRE}`
    """
)

demo.launch()
    </gradio-file>
  </gradio-lite>
</body>
</html>
