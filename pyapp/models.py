import google.generativeai as genai
from dotenv import load_dotenv
import os
from typing import List, Dict

# Cargar variables de entorno y configurar la API de Gemini
load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Modelo para la generación de respuestas con Gemini
class GeminiModel:
    @staticmethod
    async def generar_respuesta(mensaje: str) -> str:
        try:
            # Configurar el modelo y generar respuesta
            model = genai.GenerativeModel('gemini-1.5-flash')
            respuesta = await model.generate_content_async(mensaje)
            return respuesta.text
        except Exception as e:
            return f"Error: {str(e)}"
