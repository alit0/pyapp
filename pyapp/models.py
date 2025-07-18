import google.generativeai as genai
from dotenv import load_dotenv
import os
import time
from typing import List, Dict, Optional
from .file_processor import FileProcessor
from .database import procesar_comando_db

# Cargar variables de entorno y configurar la API de Gemini
load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

class GeminiModel:
    _chat_session: Optional[genai.ChatSession] = None
    _archivo_procesado: Optional[Dict] = None  # Cache del último archivo procesado
    
    @classmethod
    def get_chat_session(cls) -> genai.ChatSession:
        """Obtener o crear una sesión de chat"""
        if cls._chat_session is None:
            print("🔄 Creando nueva sesión de chat con Gemini")
            model = genai.GenerativeModel('gemini-1.5-flash')
            cls._chat_session = model.start_chat(history=[])
            print("✅ Sesión de chat creada exitosamente")
        else:
            print("♻️  Reutilizando sesión de chat existente")
        return cls._chat_session
    
    @classmethod
    def comprimir_archivo_inteligente(cls, contenido: str) -> str:
        """
        Comprime el archivo de manera inteligente manteniendo TODA la información.
        Funciona con cualquier tipo de archivo (dinámico).
        """
        print(f"🗜️  COMPRESIÓN INTELIGENTE de {len(contenido)} caracteres")
        
        # Si ya es pequeño, no comprimir
        if len(contenido) <= 60000:
            print("✅ Archivo pequeño, no necesita compresión")
            return contenido
        
        lineas = contenido.split('\n')
        print(f"📊 Procesando {len(lineas)} líneas")
        
        # Estrategia de compresión inteligente:
        # 1. Eliminar líneas vacías múltiples
        # 2. Comprimir espacios en blanco excesivos  
        # 3. Mantener estructura pero más compacta
        # 4. NO perder información de datos
        
        lineas_comprimidas = []
        linea_anterior_vacia = False
        
        for linea in lineas:
            # Limpiar espacios excesivos pero mantener estructura
            linea_limpia = ' '.join(linea.split())
            
            # Saltar líneas vacías consecutivas
            if not linea_limpia:
                if not linea_anterior_vacia:
                    lineas_comprimidas.append('')
                    linea_anterior_vacia = True
                continue
            
            linea_anterior_vacia = False
            lineas_comprimidas.append(linea_limpia)
        
        contenido_comprimido = '\n'.join(lineas_comprimidas)
        
        # Si aún es muy grande, tomar muestra representativa
        if len(contenido_comprimido) > 120000:
            print(f"⚠️  Archivo aún muy grande ({len(contenido_comprimido)} chars), tomando muestra representativa")
            
            lineas_finales = lineas_comprimidas[:2000]  # Primeras 2000 líneas
            if len(lineas_comprimidas) > 2000:
                lineas_finales.append(f"\n[NOTA: Archivo contiene {len(lineas_comprimidas)} líneas totales. Mostrando primeras 2000 líneas representativas.]")
            
            contenido_comprimido = '\n'.join(lineas_finales)
        
        reduccion = ((len(contenido) - len(contenido_comprimido)) / len(contenido)) * 100
        print(f"✅ Compresión completada:")
        print(f"  📊 Tamaño original: {len(contenido)} chars")
        print(f"  📊 Tamaño comprimido: {len(contenido_comprimido)} chars")
        print(f"  📊 Reducción: {reduccion:.1f}%")
        
        return contenido_comprimido
    
    @classmethod
    async def procesar_archivo_rapido(cls, archivo_info: Dict) -> str:
        """
        Procesa un archivo de manera rápida y eficiente.
        """
        print("🚀 PROCESANDO ARCHIVO RÁPIDO")
        nombre_archivo = archivo_info.get('name', 'archivo')
        
        # Extraer contenido del archivo
        contenido_crudo = FileProcessor.process_file(
            archivo_info.get("content", ""),
            archivo_info.get("type", ""),
            nombre_archivo
        )
        
        print(f"📄 Contenido extraído: {len(contenido_crudo)} caracteres")
        
        # Comprimir de manera inteligente
        contenido_comprimido = cls.comprimir_archivo_inteligente(contenido_crudo)
        
        # Guardar en cache
        cls._archivo_procesado = {
            'nombre': nombre_archivo,
            'contenido': contenido_comprimido,
            'contenido_original': contenido_crudo,
            'size_original': len(contenido_crudo),
            'size_procesado': len(contenido_comprimido),
            'timestamp': time.time()
        }
        
        print(f"💾 Archivo guardado en cache: {nombre_archivo}")
        return contenido_comprimido
    
    @classmethod
    def tiene_archivo_en_cache(cls, nombre_archivo: str) -> bool:
        """Verifica si un archivo ya está procesado en cache."""
        if not cls._archivo_procesado:
            return False
        return cls._archivo_procesado['nombre'] == nombre_archivo
    
    @classmethod
    def obtener_archivo_cache(cls) -> Optional[str]:
        """Obtiene el contenido del archivo desde cache."""
        if cls._archivo_procesado:
            print(f"💾 Usando archivo desde cache: {cls._archivo_procesado['nombre']}")
            return cls._archivo_procesado['contenido']
        return None
    
    @classmethod
    def limpiar_cache_archivo(cls):
        """Limpia el cache del archivo."""
        if cls._archivo_procesado:
            print(f"🗑️  Limpiando cache del archivo: {cls._archivo_procesado['nombre']}")
            cls._archivo_procesado = None
    
    @classmethod
    async def generar_respuesta(cls, mensaje: str, archivo_info: Optional[Dict] = None) -> str:
        """
        Generar respuesta rápida con compresión inteligente y manejo de base de datos.
        """
        try:
            print("=== PROCESANDO SOLICITUD RÁPIDA ===")
            print(f"📝 Mensaje: '{mensaje}'")
            inicio_total = time.time()
            
            # 🆕 VERIFICAR SI ES UN COMANDO DE BASE DE DATOS
            print("🔍 Verificando si es comando de base de datos...")
            respuesta_db = procesar_comando_db(mensaje)
            
            if respuesta_db is not None:
                print("💾 Comando de base de datos procesado")
                tiempo_total = time.time() - inicio_total
                print(f"⏱️  TIEMPO TOTAL DB: {tiempo_total:.2f}s")
                return respuesta_db
            
            print("💬 No es comando de DB, procesando con Gemini...")
            
            chat_session = cls.get_chat_session()
            
            # CASO 1: Sin archivo nuevo, pero hay archivo en cache
            if not archivo_info and cls._archivo_procesado:
                print("🔄 Consultando sobre archivo en memoria")
                contenido_archivo = cls.obtener_archivo_cache()
                nombre_archivo = cls._archivo_procesado['nombre']
                
                mensaje_completo = f"""Usuario: {mensaje}

[ARCHIVO: {nombre_archivo}]

CONTENIDO DEL ARCHIVO:
{contenido_archivo}

💾 Base de datos disponible: Puedes usar comandos como:
- "listar usuarios" - Ver todos los usuarios
- "agregar usuario [nombre] programa [programa] contraseña [contraseña]" - Crear usuario
- "buscar usuario [término]" - Buscar por nombre, ID o programa
- "modificar usuario [id] usuario [nuevo] programa [nuevo] contraseña [nueva]" - Modificar
- "eliminar usuario [id]" - Eliminar usuario
- "estadísticas" - Ver estadísticas de la BD

Instrucciones: Responde la pregunta del usuario basándote en el contenido del archivo. Si menciona usuarios o base de datos, explica que puede usar los comandos disponibles. Sé directo y profesional."""
                
                inicio_gemini = time.time()
                respuesta = await chat_session.send_message_async(mensaje_completo)
                tiempo_gemini = time.time() - inicio_gemini
                
                tiempo_total = time.time() - inicio_total
                print(f"⏱️  TIEMPO GEMINI: {tiempo_gemini:.2f}s")
                print(f"⏱️  TIEMPO TOTAL: {tiempo_total:.2f}s")
                return respuesta.text
            
            # CASO 2: Sin archivo adjunto y sin cache
            elif not archivo_info:
                print("💬 Conversación normal")
                
                # Agregar información sobre comandos de BD disponibles
                mensaje_con_db = f"""Usuario: {mensaje}

💾 SISTEMA DE BASE DE DATOS DISPONIBLE:
El usuario puede usar estos comandos para manejar la base de datos de usuarios:

📋 CONSULTAS:
- "listar usuarios" - Mostrar todos los usuarios
- "buscar usuario [término]" - Buscar por nombre, ID o programa  
- "estadísticas" - Ver estadísticas de la base de datos

➕ AGREGAR:
- "agregar usuario [nombre] programa [programa] contraseña [contraseña]"

✏️ MODIFICAR:
- "modificar usuario [id] usuario [nuevo] programa [nuevo] contraseña [nueva]"

🗑️ ELIMINAR:
- "eliminar usuario [id]"

INSTRUCCIONES: Si el usuario pregunta sobre usuarios, base de datos, o quiere realizar operaciones CRUD, explícale que puede usar estos comandos exactos. Si es una consulta general, responde normalmente."""
                
                inicio_gemini = time.time()
                respuesta = await chat_session.send_message_async(mensaje_con_db)
                tiempo_gemini = time.time() - inicio_gemini
                print(f"⏱️  TIEMPO GEMINI: {tiempo_gemini:.2f}s")
                return respuesta.text
            
            # CASO 3: Nuevo archivo adjunto
            else:
                nombre_archivo = archivo_info.get('name', 'archivo')
                print(f"📎 Procesando archivo: {nombre_archivo}")
                
                # Verificar si ya tenemos este archivo en cache
                if cls.tiene_archivo_en_cache(nombre_archivo):
                    print("♻️  Archivo ya en cache")
                    contenido_archivo = cls.obtener_archivo_cache()
                else:
                    print("🆕 Nuevo archivo, procesando...")
                    if cls._archivo_procesado:
                        cls.limpiar_cache_archivo()
                    
                    contenido_archivo = await cls.procesar_archivo_rapido(archivo_info)
                
                # UNA SOLA llamada a Gemini con contenido comprimido
                mensaje_completo = f"""Usuario: {mensaje}

[ARCHIVO: {nombre_archivo}]

CONTENIDO COMPLETO DEL ARCHIVO:
{contenido_archivo}

💾 Base de datos disponible: El usuario puede manejar usuarios con comandos como:
- "listar usuarios", "agregar usuario [datos]", "buscar usuario [término]", etc.

Instrucciones: Analiza todo el contenido del archivo y responde la pregunta del usuario. Si menciona usuarios o base de datos, explica los comandos disponibles. Sé preciso y directo."""
                
                inicio_gemini = time.time()
                respuesta = await chat_session.send_message_async(mensaje_completo)
                tiempo_gemini = time.time() - inicio_gemini
                
                tiempo_total = time.time() - inicio_total
                print(f"⏱️  TIEMPO GEMINI: {tiempo_gemini:.2f}s")
                print(f"⏱️  TIEMPO TOTAL: {tiempo_total:.2f}s")
                print(f"💾 Archivo queda en memoria para futuras consultas")
                
                return respuesta.text
            
        except Exception as e:
            error_msg = f"Error al generar respuesta: {str(e)}"
            print(f"❌ ERROR en GeminiModel: {error_msg}")
            return error_msg