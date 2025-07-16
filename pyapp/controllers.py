import reflex as rx
from typing import List, Dict
from .models import GeminiModel

class Estado(rx.State):
    mensaje: str = ""
    mensajes: List[Dict] = []
    cargando: bool = False

    async def enviar_mensaje(self):
        # No procesar si no hay mensaje o si ya está cargando
        if not self.mensaje.strip() or self.cargando:
            return

        # Poner en estado de carga
        self.cargando = True
        # Agregar mensaje del usuario a la lista
        self.mensajes.append({"texto": self.mensaje, "es_usuario": True})
        # Guardar el mensaje para enviarlo a la API y limpiar el input
        mensaje_enviado = self.mensaje
        self.mensaje = ""
        yield # Actualiza la UI para mostrar el mensaje del usuario y el spinner

        try:
            # Obtener respuesta del modelo
            respuesta = await GeminiModel.generar_respuesta(mensaje_enviado)
            
            # Agregar respuesta de la IA a la lista
            self.mensajes.append({"texto": respuesta, "es_usuario": False})
        except Exception as e:
            self.mensajes.append({"texto": f"Error: {str(e)}", "es_usuario": False})
        finally:
            # Quitar estado de carga
            self.cargando = False
            yield # Actualiza la UI para mostrar el mensaje de la IA
            
            # --- LA CLAVE DEL SCROLL ---
            # Ejecutar el script para hacer scroll después de que todo se renderizó
            yield rx.call_script(
                "document.getElementById('chat-container').scrollTop = document.getElementById('chat-container').scrollHeight"
            )

    def manejar_tecla(self, key: str):
        if key == "Enter":
            return self.enviar_mensaje
