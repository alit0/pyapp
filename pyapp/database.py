import sqlite3
import os
import secrets
import string
import time
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional

class AdminAuth:
    """Clase para manejar la autenticación de administrador."""
    
    def __init__(self):
        # Contraseña admin desde variable de entorno o default
        self.admin_password = os.getenv("ADMIN_PASSWORD", "admin123")
        self.authenticated = False
        self.auth_time = None
        self.session_duration = 300  # 5 minutos de sesión
        print(f"🔐 Sistema de autenticación admin iniciado")
        if os.getenv("ADMIN_PASSWORD"):
            print("✅ Contraseña admin cargada desde variable de entorno")
        else:
            print("⚠️  Usando contraseña admin por defecto. Configura ADMIN_PASSWORD en .env")
    
    def verificar_contraseña(self, password: str) -> bool:
        """Verificar si la contraseña admin es correcta."""
        if password == self.admin_password:
            self.authenticated = True
            self.auth_time = datetime.now()
            return True
        return False
    
    def esta_autenticado(self) -> bool:
        """Verificar si el admin está autenticado y la sesión es válida."""
        if not self.authenticated or not self.auth_time:
            return False
        
        # Verificar si la sesión ha expirado
        tiempo_transcurrido = datetime.now() - self.auth_time
        if tiempo_transcurrido.total_seconds() > self.session_duration:
            self.cerrar_sesion()
            return False
        
        return True
    
    def cerrar_sesion(self):
        """Cerrar la sesión admin."""
        self.authenticated = False
        self.auth_time = None
    
    def tiempo_restante_sesion(self) -> int:
        """Obtener tiempo restante de sesión en segundos."""
        if not self.esta_autenticado():
            return 0
        
        tiempo_transcurrido = datetime.now() - self.auth_time
        restante = self.session_duration - tiempo_transcurrido.total_seconds()
        return max(0, int(restante))
    
    def extender_sesion(self):
        """Extender la sesión actual."""
        if self.authenticated:
            self.auth_time = datetime.now()

class SimpleDatabase:
    """Clase simple para manejar la base de datos de usuarios con generador de contraseñas y autenticación admin."""
    
    def __init__(self, db_path: str = "usuarios.db"):
        self.db_path = db_path
        self.auth = AdminAuth()
        self.init_database()
        print(f"✅ Base de datos iniciada: {self.db_path}")
    
    def verificar_autenticacion(self) -> Tuple[bool, str]:
        """Verificar si el admin está autenticado."""
        if not self.auth.esta_autenticado():
            return False, "🔐 **ACCESO DENEGADO**\n\nDebes autenticarte como administrador primero.\nUsa: `auth admin [contraseña]`"
        
        # Extender sesión si está autenticado
        self.auth.extender_sesion()
        return True, ""
    
    def autenticar_admin(self, password: str) -> str:
        """Autenticar como administrador."""
        if self.auth.verificar_contraseña(password):
            tiempo_sesion = self.auth.session_duration // 60  # Convertir a minutos
            return (f"🔓 **AUTENTICACIÓN EXITOSA**\n\n"
                   f"✅ Sesión admin iniciada\n"
                   f"⏱️ Duración: {tiempo_sesion} minutos\n"
                   f"🛡️ Ahora puedes ejecutar comandos de base de datos")
        else:
            return (f"🚫 **CONTRASEÑA INCORRECTA**\n\n"
                   f"❌ Acceso denegado\n"
                   f"💡 Verifica tu contraseña de administrador")
    
    def obtener_estado_sesion(self) -> str:
        """Obtener información sobre la sesión actual."""
        if self.auth.esta_autenticado():
            tiempo_restante = self.auth.tiempo_restante_sesion()
            minutos = tiempo_restante // 60
            segundos = tiempo_restante % 60
            return (f"🔓 **SESIÓN ACTIVA**\n\n"
                   f"✅ Autenticado como administrador\n"
                   f"⏱️ Tiempo restante: {minutos}m {segundos}s\n"
                   f"🔄 Para cerrar sesión usa: `logout admin`")
        else:
            return (f"🔐 **SESIÓN CERRADA**\n\n"
                   f"❌ No estás autenticado\n"
                   f"🔑 Para acceder usa: `auth admin [contraseña]`")
    
    def cerrar_sesion_admin(self) -> str:
        """Cerrar sesión de administrador."""
        if self.auth.esta_autenticado():
            self.auth.cerrar_sesion()
            return (f"🔐 **SESIÓN CERRADA**\n\n"
                   f"✅ Sesión admin terminada\n"
                   f"🛡️ Base de datos protegida")
        else:
            return "ℹ️ No hay sesión activa para cerrar"
    
    def init_database(self):
        """Crear la tabla si no existe."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS usuarios (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    usuario TEXT NOT NULL,
                    programa TEXT NOT NULL,
                    contraseña TEXT NOT NULL,
                    fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            conn.commit()
            print("✅ Tabla usuarios creada/verificada")
    
    def generar_contraseña_compleja(self, longitud: int = 16) -> str:
        """
        Genera una contraseña segura con una mezcla de tipos de caracteres.
        
        Args:
            longitud (int): La longitud deseada para la contraseña. Mínimo 8.
            
        Returns:
            str: La contraseña generada.
        """
        if longitud < 8:
            longitud = 8  # Mínimo de seguridad
        
        # Definir los conjuntos de caracteres a utilizar
        letras_minusculas = string.ascii_lowercase
        letras_mayusculas = string.ascii_uppercase
        numeros = string.digits
        simbolos = "!@#$%&*+-=?"  # Símbolos seguros (evitamos algunos problemáticos)
        
        # Combinar todos los caracteres en un solo alfabeto
        alfabeto = letras_minusculas + letras_mayusculas + numeros + simbolos
        
        max_intentos = 100  # Evitar bucle infinito
        for intento in range(max_intentos):
            # Generar una contraseña eligiendo caracteres del alfabeto
            contraseña = ''.join(secrets.choice(alfabeto) for _ in range(longitud))
            
            # Asegurarse de que la contraseña contenga al menos un carácter de cada tipo
            if (any(c in letras_minusculas for c in contraseña)
                    and any(c in letras_mayusculas for c in contraseña)
                    and any(c in numeros for c in contraseña)
                    and any(c in simbolos for c in contraseña)):
                return contraseña
        
        # Si después de 100 intentos no se genera una contraseña válida, forzar una
        # Esto es muy improbable, pero por seguridad
        return (secrets.choice(letras_minusculas) + 
                secrets.choice(letras_mayusculas) + 
                secrets.choice(numeros) + 
                secrets.choice(simbolos) + 
                ''.join(secrets.choice(alfabeto) for _ in range(longitud - 4)))
    
    def agregar_usuario(self, usuario: str, programa: str, contraseña: str = None, longitud_contraseña: int = 16) -> str:
        """
        Agregar un nuevo usuario. Si no se proporciona contraseña, se genera automáticamente.
        REQUIERE AUTENTICACIÓN ADMIN.
        """
        # Verificar autenticación
        autenticado, mensaje_error = self.verificar_autenticacion()
        if not autenticado:
            return mensaje_error
        
        try:
            # Si no se proporciona contraseña, generar una automáticamente
            if not contraseña:
                contraseña_generada = self.generar_contraseña_compleja(longitud_contraseña)
                mensaje_contraseña = f"🔐 Contraseña generada automáticamente: {contraseña_generada}"
            else:
                contraseña_generada = contraseña
                mensaje_contraseña = f"🔐 Contraseña personalizada establecida"
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO usuarios (usuario, programa, contraseña, fecha)
                    VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                ''', (usuario, programa, contraseña_generada))
                conn.commit()
                
                resultado = f"✅ Usuario '{usuario}' agregado exitosamente con ID {cursor.lastrowid}\n"
                resultado += f"👤 Usuario: {usuario}\n"
                resultado += f"💻 Programa: {programa}\n"
                resultado += f"{mensaje_contraseña}\n"
                resultado += f"🔐 Operación autorizada por admin"
                
                return resultado
                
        except sqlite3.IntegrityError:
            return f"❌ Error: Ya existe un usuario con datos similares"
        except Exception as e:
            return f"❌ Error al agregar usuario: {str(e)}"
    
    def obtener_usuarios(self, limite: int = None) -> str:
        """Obtener lista de todos los usuarios. REQUIERE AUTENTICACIÓN ADMIN."""
        # Verificar autenticación
        autenticado, mensaje_error = self.verificar_autenticacion()
        if not autenticado:
            return mensaje_error
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                query = "SELECT id, usuario, programa, contraseña, fecha FROM usuarios ORDER BY fecha DESC"
                if limite:
                    query += f" LIMIT {limite}"
                
                cursor.execute(query)
                usuarios = cursor.fetchall()
                
                if not usuarios:
                    return "📋 No hay usuarios registrados en la base de datos."
                
                resultado = f"📋 Lista de usuarios ({len(usuarios)} total) - 🔐 Acceso autorizado:\n\n"
                for user in usuarios:
                    resultado += f"🔹 ID: {user[0]}\n"
                    resultado += f"   Usuario: {user[1]}\n"
                    resultado += f"   Programa: {user[2]}\n"
                    resultado += f"   Contraseña: {user[3]}\n"
                    resultado += f"   Fecha: {user[4]}\n\n"
                
                return resultado
        except Exception as e:
            return f"❌ Error al obtener usuarios: {str(e)}"
    
    def buscar_usuario(self, busqueda: str) -> str:
        """Buscar usuario por ID, nombre de usuario o programa. REQUIERE AUTENTICACIÓN ADMIN."""
        # Verificar autenticación
        autenticado, mensaje_error = self.verificar_autenticacion()
        if not autenticado:
            return mensaje_error
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Buscar por ID si es número
                if busqueda.isdigit():
                    cursor.execute("SELECT * FROM usuarios WHERE id = ?", (int(busqueda),))
                else:
                    # Buscar por usuario o programa
                    cursor.execute('''
                        SELECT * FROM usuarios 
                        WHERE usuario LIKE ? OR programa LIKE ?
                    ''', (f'%{busqueda}%', f'%{busqueda}%'))
                
                usuarios = cursor.fetchall()
                
                if not usuarios:
                    return f"❌ No se encontraron usuarios que coincidan con '{busqueda}'"
                
                resultado = f"🔍 Resultados de búsqueda para '{busqueda}' - 🔐 Acceso autorizado:\n\n"
                for user in usuarios:
                    resultado += f"🔹 ID: {user[0]} | Usuario: {user[1]} | Programa: {user[2]} | Contraseña: {user[3]} | Fecha: {user[4]}\n"
                
                return resultado
        except Exception as e:
            return f"❌ Error en búsqueda: {str(e)}"
    
    def modificar_usuario(self, user_id: int, usuario: str = None, programa: str = None, contraseña: str = None) -> str:
        """Modificar un usuario existente. REQUIERE AUTENTICACIÓN ADMIN."""
        # Verificar autenticación
        autenticado, mensaje_error = self.verificar_autenticacion()
        if not autenticado:
            return mensaje_error
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Verificar que el usuario existe
                cursor.execute("SELECT * FROM usuarios WHERE id = ?", (user_id,))
                if not cursor.fetchone():
                    return f"❌ No existe usuario con ID {user_id}"
                
                # Construir la consulta de actualización
                campos = []
                valores = []
                
                if usuario:
                    campos.append("usuario = ?")
                    valores.append(usuario)
                
                if programa:
                    campos.append("programa = ?")
                    valores.append(programa)
                
                if contraseña:
                    campos.append("contraseña = ?")
                    valores.append(contraseña)
                
                if not campos:
                    return "❌ No se especificaron campos para modificar"
                
                # Siempre actualizar la fecha
                campos.append("fecha = CURRENT_TIMESTAMP")
                valores.append(user_id)
                
                query = f"UPDATE usuarios SET {', '.join(campos)} WHERE id = ?"
                cursor.execute(query, valores)
                conn.commit()
                
                return f"✅ Usuario con ID {user_id} modificado exitosamente - 🔐 Operación autorizada por admin"
        except Exception as e:
            return f"❌ Error al modificar usuario: {str(e)}"
    
    def eliminar_usuario(self, user_id: int) -> str:
        """Eliminar un usuario por ID. REQUIERE AUTENTICACIÓN ADMIN."""
        # Verificar autenticación
        autenticado, mensaje_error = self.verificar_autenticacion()
        if not autenticado:
            return mensaje_error
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Verificar que el usuario existe
                cursor.execute("SELECT usuario FROM usuarios WHERE id = ?", (user_id,))
                result = cursor.fetchone()
                if not result:
                    return f"❌ No existe usuario con ID {user_id}"
                
                nombre_usuario = result[0]
                
                # Eliminar el usuario
                cursor.execute("DELETE FROM usuarios WHERE id = ?", (user_id,))
                conn.commit()
                
                return f"✅ Usuario '{nombre_usuario}' (ID {user_id}) eliminado exitosamente - 🔐 Operación autorizada por admin"
        except Exception as e:
            return f"❌ Error al eliminar usuario: {str(e)}"
    
    def regenerar_contraseña(self, user_id: int, longitud: int = 16) -> str:
        """
        Regenerar automáticamente la contraseña de un usuario. REQUIERE AUTENTICACIÓN ADMIN.
        """
        # Verificar autenticación
        autenticado, mensaje_error = self.verificar_autenticacion()
        if not autenticado:
            return mensaje_error
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Verificar que el usuario existe
                cursor.execute("SELECT usuario FROM usuarios WHERE id = ?", (user_id,))
                result = cursor.fetchone()
                if not result:
                    return f"❌ No existe usuario con ID {user_id}"
                
                nombre_usuario = result[0]
                
                # Generar nueva contraseña
                nueva_contraseña = self.generar_contraseña_compleja(longitud)
                
                # Actualizar la contraseña
                cursor.execute('''
                    UPDATE usuarios 
                    SET contraseña = ?, fecha = CURRENT_TIMESTAMP 
                    WHERE id = ?
                ''', (nueva_contraseña, user_id))
                conn.commit()
                
                return (f"🔄 Contraseña regenerada para '{nombre_usuario}' (ID {user_id})\n"
                       f"🔐 Nueva contraseña: {nueva_contraseña}\n"
                       f"🔐 Operación autorizada por admin")
                
        except Exception as e:
            return f"❌ Error al regenerar contraseña: {str(e)}"
    
    def obtener_estadisticas(self) -> str:
        """Obtener estadísticas de la base de datos. REQUIERE AUTENTICACIÓN ADMIN."""
        # Verificar autenticación
        autenticado, mensaje_error = self.verificar_autenticacion()
        if not autenticado:
            return mensaje_error
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Total usuarios
                cursor.execute("SELECT COUNT(*) FROM usuarios")
                total = cursor.fetchone()[0]
                
                # Programas más usados
                cursor.execute('''
                    SELECT programa, COUNT(*) as cantidad 
                    FROM usuarios 
                    GROUP BY programa 
                    ORDER BY cantidad DESC 
                    LIMIT 5
                ''')
                programas = cursor.fetchall()
                
                # Usuario más reciente
                cursor.execute('''
                    SELECT usuario, fecha 
                    FROM usuarios 
                    ORDER BY fecha DESC 
                    LIMIT 1
                ''')
                reciente = cursor.fetchone()
                
                resultado = f"📊 Estadísticas de la base de datos - 🔐 Acceso autorizado:\n\n"
                resultado += f"👥 Total de usuarios: {total}\n\n"
                
                if programas:
                    resultado += "🏆 Programas más usados:\n"
                    for programa, cantidad in programas:
                        resultado += f"   • {programa}: {cantidad} usuarios\n"
                    resultado += "\n"
                
                if reciente:
                    resultado += f"🆕 Usuario más reciente: {reciente[0]} ({reciente[1]})\n"
                
                return resultado
        except Exception as e:
            return f"❌ Error al obtener estadísticas: {str(e)}"

# Instancia global
db = SimpleDatabase()

# Funciones de conveniencia
def procesar_comando_db(mensaje: str) -> str:
    """
    Procesar comandos de base de datos desde el chat.
    Esta función interpreta el mensaje y ejecuta la operación correspondiente.
    """
    mensaje_lower = mensaje.lower().strip()
    
    # ========== COMANDOS DE AUTENTICACIÓN (NO REQUIEREN AUTH) ==========
    
    # Comando para autenticarse como admin
    if mensaje_lower.startswith("auth admin"):
        try:
            partes = mensaje.split()
            if len(partes) >= 3:
                password = " ".join(partes[2:])
                return db.autenticar_admin(password)
            else:
                return "❌ Formato: 'auth admin [contraseña]'"
        except:
            return "❌ Formato: 'auth admin [contraseña]'"
    
    # Comando para ver estado de sesión
    elif "session status" in mensaje_lower or "estado sesion" in mensaje_lower:
        return db.obtener_estado_sesion()
    
    # Comando para cerrar sesión
    elif "logout admin" in mensaje_lower or "cerrar sesion" in mensaje_lower:
        return db.cerrar_sesion_admin()
    
    # Comando para generar contraseña (NO REQUIERE AUTH - es solo una herramienta)
    elif "generar contraseña" in mensaje_lower:
        try:
            longitud = 16  # Default
            
            # Buscar longitud personalizada
            if "longitud" in mensaje_lower:
                partes = mensaje.split()
                try:
                    idx_longitud = next(i for i, word in enumerate(partes) if word.lower() == "longitud")
                    longitud = int(partes[idx_longitud + 1])
                except:
                    pass
            
            contraseña_generada = db.generar_contraseña_compleja(longitud)
            return (f"🔐 Contraseña generada (longitud {longitud}):\n"
                   f"**{contraseña_generada}**\n\n"
                   f"✅ La contraseña incluye:\n"
                   f"• Letras mayúsculas y minúsculas\n"
                   f"• Números\n"
                   f"• Símbolos especiales\n"
                   f"• Generada con seguridad criptográfica\n\n"
                   f"ℹ️ Este comando no requiere autenticación admin")
        except:
            return "❌ Formato: 'generar contraseña' o 'generar contraseña longitud [número]'"
    
    # ========== COMANDOS QUE REQUIEREN AUTENTICACIÓN ADMIN ==========
    
    # Comandos para agregar usuario
    elif "agregar usuario" in mensaje_lower or "crear usuario" in mensaje_lower:
        try:
            partes = mensaje.split()
            
            # Formato 1: "agregar usuario [nombre] programa [programa]" (sin contraseña - auto-generar)
            if "programa" in mensaje_lower and "contraseña" not in mensaje_lower:
                idx_programa = next(i for i, word in enumerate(partes) if word.lower() == "programa")
                usuario = " ".join(partes[2:idx_programa])
                programa = " ".join(partes[idx_programa+1:])
                
                # Verificar si se especifica longitud de contraseña
                longitud = 16  # Default
                if "longitud" in mensaje_lower:
                    try:
                        idx_longitud = next(i for i, word in enumerate(partes) if word.lower() == "longitud")
                        longitud = int(partes[idx_longitud + 1])
                        programa = " ".join(partes[idx_programa+1:idx_longitud])  # Ajustar programa
                    except:
                        pass
                
                return db.agregar_usuario(usuario, programa, longitud_contraseña=longitud)
            
            # Formato 2: "agregar usuario [nombre] programa [programa] contraseña [contraseña]" (contraseña manual)
            elif "programa" in mensaje_lower and "contraseña" in mensaje_lower:
                idx_programa = next(i for i, word in enumerate(partes) if word.lower() == "programa")
                idx_contraseña = next(i for i, word in enumerate(partes) if word.lower() == "contraseña")
                
                usuario = " ".join(partes[2:idx_programa])
                programa = " ".join(partes[idx_programa+1:idx_contraseña])
                contraseña = " ".join(partes[idx_contraseña+1:])
                
                return db.agregar_usuario(usuario, programa, contraseña)
            
            else:
                return ("❌ Formato:\n"
                       "• 'agregar usuario [nombre] programa [programa]' (contraseña automática)\n"
                       "• 'agregar usuario [nombre] programa [programa] longitud [número]' (contraseña auto con longitud)\n"
                       "• 'agregar usuario [nombre] programa [programa] contraseña [contraseña]' (contraseña manual)\n\n"
                       "🔐 **REQUIERE AUTENTICACIÓN ADMIN**")
        except:
            return ("❌ Error en formato. Usa:\n"
                   "• 'agregar usuario Juan programa AutoCAD' (contraseña automática)\n"
                   "• 'agregar usuario Juan programa AutoCAD longitud 20' (contraseña auto de 20 chars)\n"
                   "• 'agregar usuario Juan programa AutoCAD contraseña mi_pass_123' (manual)\n\n"
                   "🔐 **REQUIERE AUTENTICACIÓN ADMIN**")
    
    # Comandos para regenerar contraseña
    elif "regenerar contraseña" in mensaje_lower or "nueva contraseña" in mensaje_lower:
        try:
            partes = mensaje.split()
            
            # Buscar el ID
            id_usuario = None
            longitud = 16  # Default
            
            for i, parte in enumerate(partes):
                if parte.isdigit():
                    id_usuario = int(parte)
                    break
                    
            if id_usuario is None:
                return "❌ Formato: 'regenerar contraseña [id]' o 'regenerar contraseña [id] longitud [número]'\n\n🔐 **REQUIERE AUTENTICACIÓN ADMIN**"
            
            # Buscar longitud personalizada
            if "longitud" in mensaje_lower:
                try:
                    idx_longitud = next(i for i, word in enumerate(partes) if word.lower() == "longitud")
                    longitud = int(partes[idx_longitud + 1])
                except:
                    pass
            
            return db.regenerar_contraseña(id_usuario, longitud)
        except:
            return "❌ Formato: 'regenerar contraseña [id]' o 'regenerar contraseña [id] longitud [número]'\n\n🔐 **REQUIERE AUTENTICACIÓN ADMIN**"
    
    # Comandos para listar usuarios
    elif "listar usuarios" in mensaje_lower or "mostrar usuarios" in mensaje_lower or "ver usuarios" in mensaje_lower:
        return db.obtener_usuarios()
    
    # Comandos para buscar usuario
    elif "buscar usuario" in mensaje_lower:
        try:
            busqueda = mensaje.split("buscar usuario", 1)[1].strip()
            if busqueda:
                return db.buscar_usuario(busqueda)
            else:
                return "❌ Especifica qué buscar: 'buscar usuario [nombre/id/programa]'\n\n🔐 **REQUIERE AUTENTICACIÓN ADMIN**"
        except:
            return "❌ Formato: 'buscar usuario [nombre/id/programa]'\n\n🔐 **REQUIERE AUTENTICACIÓN ADMIN**"
    
    # Comandos para modificar usuario
    elif "modificar usuario" in mensaje_lower:
        try:
            # Formato más simple: "modificar usuario [id] [campo] [valor]"
            partes = mensaje.split()
            
            if len(partes) < 4:
                return "❌ Formato: 'modificar usuario [id] [campo] [valor]'\n\n🔐 **REQUIERE AUTENTICACIÓN ADMIN**"
            
            id_usuario = int(partes[2])
            
            # Obtener el resto del mensaje después del ID
            resto_mensaje = " ".join(partes[3:])
            
            nuevo_usuario = None
            nuevo_programa = None
            nueva_contraseña = None
            
            # Detectar qué campo se quiere modificar
            if resto_mensaje.startswith("contraseña "):
                nueva_contraseña = resto_mensaje.replace("contraseña ", "", 1).strip()
            elif resto_mensaje.startswith("programa "):
                nuevo_programa = resto_mensaje.replace("programa ", "", 1).strip()
            elif resto_mensaje.startswith("usuario "):
                nuevo_usuario = resto_mensaje.replace("usuario ", "", 1).strip()
            else:
                # Formato complejo: buscar palabras clave
                if " contraseña " in resto_mensaje:
                    idx = resto_mensaje.find(" contraseña ")
                    nueva_contraseña = resto_mensaje[idx + 12:].strip()
                
                if " programa " in resto_mensaje:
                    idx = resto_mensaje.find(" programa ")
                    end_idx = resto_mensaje.find(" contraseña ")
                    if end_idx == -1:
                        end_idx = len(resto_mensaje)
                    nuevo_programa = resto_mensaje[idx + 10:end_idx].strip()
                
                if resto_mensaje.startswith("usuario "):
                    end_idx = resto_mensaje.find(" programa ")
                    if end_idx == -1:
                        end_idx = resto_mensaje.find(" contraseña ")
                    if end_idx == -1:
                        end_idx = len(resto_mensaje)
                    nuevo_usuario = resto_mensaje[8:end_idx].strip()
            
            if not nuevo_usuario and not nuevo_programa and not nueva_contraseña:
                return "❌ Especifica qué modificar: 'modificar usuario [id] contraseña [nueva]' o 'modificar usuario [id] programa [nuevo]'\n\n🔐 **REQUIERE AUTENTICACIÓN ADMIN**"
            
            return db.modificar_usuario(id_usuario, nuevo_usuario, nuevo_programa, nueva_contraseña)
            
        except ValueError:
            return "❌ ID debe ser un número. Formato: 'modificar usuario [id] contraseña [nueva]'\n\n🔐 **REQUIERE AUTENTICACIÓN ADMIN**"
        except Exception as e:
            return f"❌ Error: {str(e)}. Formato: 'modificar usuario [id] contraseña [nueva]'\n\n🔐 **REQUIERE AUTENTICACIÓN ADMIN**"
    
    # Comandos para eliminar usuario
    elif "eliminar usuario" in mensaje_lower or "borrar usuario" in mensaje_lower:
        try:
            # Buscar el ID
            partes = mensaje.split()
            id_usuario = int(partes[2])
            return db.eliminar_usuario(id_usuario)
        except:
            return "❌ Formato: 'eliminar usuario [id]'\n\n🔐 **REQUIERE AUTENTICACIÓN ADMIN**"
    
    # Comandos para estadísticas
    elif "estadisticas" in mensaje_lower or "estadísticas" in mensaje_lower:
        return db.obtener_estadisticas()
    
    # Comando de ayuda
    elif "ayuda db" in mensaje_lower or "help db" in mensaje_lower:
        return (f"🔐 **COMANDOS DE BASE DE DATOS**\n\n"
               f"**AUTENTICACIÓN:**\n"
               f"• `auth admin [contraseña]` - Autenticarse como admin\n"
               f"• `session status` - Ver estado de sesión\n"
               f"• `logout admin` - Cerrar sesión\n\n"
               f"**SIN AUTENTICACIÓN:**\n"
               f"• `generar contraseña [longitud]` - Generar contraseña\n"
               f"• `ayuda db` - Mostrar esta ayuda\n\n"
               f"**CON AUTENTICACIÓN ADMIN:**\n"
               f"• `agregar usuario [nombre] programa [programa]` - Crear usuario\n"
               f"• `listar usuarios` - Ver todos los usuarios\n"
               f"• `buscar usuario [término]` - Buscar usuario\n"
               f"• `modificar usuario [id] [campo] [valor]` - Modificar usuario\n"
               f"• `eliminar usuario [id]` - Eliminar usuario\n"
               f"• `regenerar contraseña [id]` - Nueva contraseña\n"
               f"• `estadísticas` - Ver estadísticas\n\n"
               f"🛡️ **SEGURIDAD:** Sesiones admin duran 5 minutos")
    
    # Si no es un comando de BD, retornar None para que Gemini procese normal
    return None