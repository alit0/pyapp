import reflex as rx
from typing import List, Dict, Any
import base64
from .models import GeminiModel

class Estado(rx.State):
    mensaje: str = ""
    mensajes: List[Dict] = []
    cargando: bool = False
    archivo_adjunto: Dict[str, Any] = {}
    mostrar_adjunto: bool = False

    async def enviar_mensaje(self):
        # No procesar si no hay mensaje o si ya está cargando
        mensaje_vacio = len(self.mensaje.strip()) == 0
        archivo_vacio = len(self.archivo_adjunto) == 0
        
        # Usar rx.cond para evaluar condiciones con variables de estado
        if mensaje_vacio and archivo_vacio or self.cargando:
            return

        # Poner en estado de carga
        self.cargando = True
        
        # Preparar el mensaje con o sin archivo adjunto
        texto_mensaje = self.mensaje.strip()
        tiene_adjunto = bool(self.archivo_adjunto)
        
        # Crear el mensaje para mostrar al usuario
        mensaje_usuario = {
            "texto": texto_mensaje,
            "es_usuario": True,
            "tiene_adjunto": tiene_adjunto,
            "nombre_archivo": self.archivo_adjunto.get("name", "") if tiene_adjunto else ""
        }
        
        # Agregar mensaje del usuario a la lista
        self.mensajes.append(mensaje_usuario)
        
        # Guardar el mensaje para enviarlo a la API y limpiar el input
        mensaje_enviado = texto_mensaje
        self.mensaje = ""
        
        # Limpiar el archivo adjunto después de enviarlo
        archivo_para_enviar = self.archivo_adjunto
        self.archivo_adjunto = {}
        self.mostrar_adjunto = False
        
        yield # Actualiza la UI para mostrar el mensaje del usuario y el spinner

        try:
            # Obtener respuesta del modelo
            if tiene_adjunto:
                # Si hay archivo adjunto, incluirlo en el mensaje
                contenido_archivo = archivo_para_enviar.get("content", "")
                tipo_archivo = archivo_para_enviar.get("type", "")
                nombre_archivo = archivo_para_enviar.get("name", "")
                
                mensaje_con_adjunto = f"{mensaje_enviado}\n\n[Archivo adjunto: {nombre_archivo} ({tipo_archivo})]\n"
                respuesta = await GeminiModel.generar_respuesta(mensaje_con_adjunto)
            else:
                # Si no hay archivo, enviar solo el texto
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
    
    def adjuntar_archivo(self, name: str, type: str, size: int, content: str):
        """Manejar la subida de archivos."""
        # Guardar información del archivo
        self.archivo_adjunto = {
            "name": name,
            "type": type,
            "size": size,
            "content": content
        }
        
        # Mostrar el nombre del archivo adjunto
        self.mostrar_adjunto = True
    
    def eliminar_adjunto(self):
        """Eliminar el archivo adjunto."""
        self.archivo_adjunto = {}
        self.mostrar_adjunto = False
