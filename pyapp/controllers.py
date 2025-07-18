import reflex as rx
from typing import List, Dict, Any
import base64
import time
from .models import GeminiModel

class Estado(rx.State):
    mensaje: str = ""
    mensajes: List[Dict] = []
    cargando: bool = False
    archivo_adjunto: Dict[str, Any] = {}
    mostrar_adjunto: bool = False

    @rx.var
    def tamaño_archivo_formateado(self) -> str:
        """Retorna el tamaño del archivo formateado en KB."""
        if self.archivo_adjunto and "size" in self.archivo_adjunto:
            size_kb = self.archivo_adjunto["size"] / 1024
            return f"({size_kb:.1f} KB)"
        return ""

    @rx.event
    async def handle_upload(self, files: List[rx.UploadFile]):
        """Manejar la subida de archivos usando el patrón oficial de Reflex."""
        print("=== UPLOAD HANDLER LLAMADO (PATRÓN OFICIAL) ===")
        print(f"📁 Archivos recibidos: {len(files)}")
        
        if not files:
            print("❌ No se recibieron archivos")
            return
        
        # Tomar solo el primer archivo
        file = files[0]
        print(f"📄 Procesando archivo: {file.name}")  # Cambiado de filename a name
        print(f"🏷️  Tipo: {file.content_type}")
        
        # Leer el archivo para obtener el tamaño
        upload_data = await file.read()
        file_size = len(upload_data)
        print(f"📏 Tamaño: {file_size} bytes")
        
        # Validar tipos de archivo soportados
        extensiones_soportadas = ['.pdf', '.docx', '.xlsx', '.xls', '.txt']
        extension = '.' + file.name.split('.')[-1].lower() if '.' in file.name else ''
        
        print(f"🔍 Extensión detectada: {extension}")
        
        if extension not in extensiones_soportadas:
            print(f"❌ Extensión no soportada: {extension}")
            self.mensajes.append({
                "texto": f"Tipo de archivo no soportado: {file.name}. Solo se admiten archivos PDF, DOCX, XLSX y TXT.",
                "es_usuario": False
            })
            return
        
        # Validar tamaño del archivo (máximo 10MB)
        max_size = 10 * 1024 * 1024  # 10MB en bytes
        if file_size > max_size:
            print(f"❌ Archivo demasiado grande: {file_size} bytes (máximo: {max_size} bytes)")
            self.mensajes.append({
                "texto": f"El archivo {file.name} es demasiado grande. El tamaño máximo permitido es 10MB.",
                "es_usuario": False
            })
            return
        
        print("✅ Validaciones pasadas correctamente")
        
        try:
            print("📖 Procesando contenido del archivo...")
            
            # Convertir a base64 para almacenar
            content_base64 = base64.b64encode(upload_data).decode('utf-8')
            data_url = f"data:{file.content_type or 'application/octet-stream'};base64,{content_base64}"
            
            # Guardar información del archivo
            self.archivo_adjunto = {
                "name": file.name,
                "type": file.content_type or "",
                "size": file_size,
                "content": data_url
            }
            
            # Mostrar el nombre del archivo adjunto
            self.mostrar_adjunto = True
            print(f"✅ Archivo guardado y listo para enviar: {file.name}")
            
            # Limpiar archivos seleccionados
            yield rx.clear_selected_files("file_upload")
            
        except Exception as e:
            error_msg = f"Error al procesar el archivo: {str(e)}"
            print(f"❌ {error_msg}")
            self.mensajes.append({
                "texto": error_msg,
                "es_usuario": False
            })

    async def enviar_mensaje(self):
        print("=== INICIANDO ENVÍO DE MENSAJE ===")
        inicio_tiempo = time.time()
        
        # No procesar si no hay mensaje o si ya está cargando
        mensaje_vacio = len(self.mensaje.strip()) == 0
        archivo_vacio = len(self.archivo_adjunto) == 0
        
        print(f"Mensaje vacío: {mensaje_vacio}")
        print(f"Archivo vacío: {archivo_vacio}")
        print(f"Cargando: {self.cargando}")
        
        # Usar rx.cond para evaluar condiciones con variables de estado
        if mensaje_vacio and archivo_vacio or self.cargando:
            print("❌ No se puede enviar: mensaje y archivo vacíos o ya está cargando")
            return

        # Poner en estado de carga
        self.cargando = True
        
        # Preparar el mensaje con o sin archivo adjunto
        texto_mensaje = self.mensaje.strip()
        tiene_adjunto = bool(self.archivo_adjunto)
        
        print(f"📝 Texto del mensaje: '{texto_mensaje}'")
        print(f"📎 Tiene archivo adjunto: {tiene_adjunto}")
        
        if tiene_adjunto:
            print(f"📄 Archivo adjunto:")
            print(f"  - Nombre: {self.archivo_adjunto.get('name', 'N/A')}")
            print(f"  - Tipo: {self.archivo_adjunto.get('type', 'N/A')}")
            print(f"  - Tamaño: {self.archivo_adjunto.get('size', 0)} bytes")
        
        # Crear el mensaje para mostrar al usuario
        mensaje_usuario = {
            "texto": texto_mensaje,
            "es_usuario": True,
            "tiene_adjunto": tiene_adjunto,
            "nombre_archivo": self.archivo_adjunto.get("name", "") if tiene_adjunto else ""
        }
        
        # Agregar mensaje del usuario a la lista
        self.mensajes.append(mensaje_usuario)
        print("✅ Mensaje del usuario agregado a la lista")
        
        # Guardar el mensaje para enviarlo a la API y limpiar el input
        mensaje_enviado = texto_mensaje
        self.mensaje = ""
        
        # Guardar archivo para enviar y limpiar después
        archivo_para_enviar = self.archivo_adjunto.copy() if tiene_adjunto else None
        self.archivo_adjunto = {}
        self.mostrar_adjunto = False
        
        print("🧹 Estado limpiado (mensaje e input)")
        
        yield # Actualiza la UI para mostrar el mensaje del usuario y el spinner

        try:
            print("🤖 Enviando a Gemini...")
            tiempo_inicio_gemini = time.time()
            
            # Obtener respuesta del modelo
            if tiene_adjunto and archivo_para_enviar:
                print("📎 Enviando mensaje CON archivo adjunto")
                respuesta = await GeminiModel.generar_respuesta(
                    mensaje_enviado, 
                    archivo_para_enviar
                )
            else:
                print("💬 Enviando mensaje SIN archivo adjunto")
                respuesta = await GeminiModel.generar_respuesta(mensaje_enviado)
            
            tiempo_respuesta = time.time() - tiempo_inicio_gemini
            print(f"⏱️  TIEMPO DE RESPUESTA DE GEMINI: {tiempo_respuesta:.2f} segundos")
            print(f"✅ Respuesta recibida de Gemini (longitud: {len(respuesta)} caracteres)")
            print(f"📄 Primeros 100 caracteres: {respuesta[:100]}...")
            
            # Agregar respuesta de la IA a la lista
            self.mensajes.append({"texto": respuesta, "es_usuario": False})
            print("✅ Respuesta de IA agregada a la lista")
            
        except Exception as e:
            error_msg = f"Error al procesar la solicitud: {str(e)}"
            print(f"❌ ERROR: {error_msg}")
            self.mensajes.append({"texto": error_msg, "es_usuario": False})
            
        finally:
            # Quitar estado de carga
            self.cargando = False
            tiempo_total = time.time() - inicio_tiempo
            print(f"⏱️  TIEMPO TOTAL DEL PROCESO: {tiempo_total:.2f} segundos")
            print("🏁 Proceso completado, carga finalizada")
            yield # Actualiza la UI para mostrar el mensaje de la IA
            
            # Ejecutar el script para hacer scroll después de que todo se renderizó
            yield rx.call_script(
                "document.getElementById('chat-container').scrollTop = document.getElementById('chat-container').scrollHeight"
            )

    def manejar_tecla(self, key: str):
        if key == "Enter":
            return self.enviar_mensaje
    
    def eliminar_adjunto(self):
        """Eliminar el archivo adjunto."""
        print("🗑️  Eliminando archivo adjunto")
        archivo_eliminado = self.archivo_adjunto.get("name", "archivo")
        self.archivo_adjunto = {}
        self.mostrar_adjunto = False
        print(f"✅ Archivo eliminado: {archivo_eliminado}")