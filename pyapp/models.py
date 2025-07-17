import google.generativeai as genai
from dotenv import load_dotenv
import os
from typing import List, Dict, Optional

# Cargar variables de entorno y configurar la API de Gemini
load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Modelo para la generación de respuestas con Gemini usando ChatSession para memoria
class GeminiModel:
    _chat_session: Optional[genai.ChatSession] = None
    
    @classmethod
    def get_chat_session(cls) -> genai.ChatSession:
        """Obtener o crear una sesión de chat"""
        if cls._chat_session is None:
            model = genai.GenerativeModel('gemini-1.5-flash')
            cls._chat_session = model.start_chat(history=[])
        return cls._chat_session
    
    @classmethod
    async def generar_respuesta(cls, mensaje: str) -> str:
        """Generar respuesta usando la sesión de chat para mantener el historial"""
        try:
            # Usar la sesión de chat para enviar el mensaje (incluye automáticamente el historial)
            chat_session = cls.get_chat_session()
            respuesta = await chat_session.send_message_async(mensaje)
            return respuesta.text
        except Exception as e:
            return f"Error: {str(e)}"
