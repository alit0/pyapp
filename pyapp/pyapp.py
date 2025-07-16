import reflex as rx
from typing import Optional
import os
import time
from dotenv import load_dotenv
import google.generativeai as genai

# Cargar variables de entorno
load_dotenv()

# Obtener la API key de las variables de entorno
API_KEY = os.getenv("GOOGLE_API_KEY", "AIzaSyA_aGYirvIIz7l7rLIrdZDajgORHy-aXuA")

# Configurar la API key globalmente
genai.configure(api_key=API_KEY)

# Configuración de estilo para toda la aplicación
app_style = {
    "font_family": "Inter, system-ui, sans-serif",
    "background": "#F5F5F5",
    "border_radius": "xl",
    "shadow": "lg",
}

# Tema personalizado para la aplicación
app_theme = rx.theme(
    accent_color="purple",
    radius="large",  # Valores válidos: 'none', 'small', 'medium', 'large', 'full'
)

# Importar la biblioteca de Google Generative AI
try:
    import google.generativeai as genai
    print("Biblioteca google.generativeai importada correctamente")
    # Configurar la API key globalmente
    genai.configure(api_key=API_KEY)
    print(f"API de Gemini configurada con la clave: {API_KEY[:5]}...")
except ImportError:
    try:
        import google.genai as genai
        print("Biblioteca google.genai importada correctamente")
        # Configurar la API key globalmente
        genai.configure(api_key=API_KEY)
        print(f"API de Gemini configurada con la clave: {API_KEY[:5]}... (usando google.genai)")
    except ImportError:
        print("Error: No se pudo importar la biblioteca de Google Generative AI")
        genai = None

class ChatState(rx.State):
    # Estado para almacenar el mensaje actual y la lista de mensajes
    mensaje: str = ""
    mensajes: list[dict] = []
    api_key: str = API_KEY  # Usar la variable global definida arriba
    is_loading: bool = False
    error_message: Optional[str] = None
    scroll_id: int = 0  # ID para forzar el desplazamiento
    
    def on_load(self):
        # Asegurarse de que la API esté configurada
        if genai is not None and self.api_key:
            try:
                # Configurar explícitamente la API key
                genai.configure(api_key=self.api_key)
                print(f"API key configurada en on_load: {self.api_key[:5]}...")
            except Exception as e:
                print(f"Error al configurar API key: {str(e)}")
    
    def set_api_key(self, api_key: str):
        """Establecer la API key de Gemini"""
        self.api_key = api_key
        # Configurar la API de Gemini
        genai.configure(api_key=api_key)
    
    def handle_key_press(self, key: str):
        """Manejar eventos de teclado para enviar mensajes con Enter"""
        if key == "Enter" and not self.is_loading and self.mensaje.strip():
            # Llamar directamente al método enviar_mensaje
            self.enviar_mensaje()
    
    def scroll_to_bottom(self):
        """Forzar el desplazamiento al fondo del chat."""
        # Incrementar el ID de scroll para forzar la actualización
        self.scroll_id += 1
        # Ejecutar un script para forzar el scroll
        return rx.call_script(
            """
            setTimeout(function() {
                const chatContainer = document.getElementById('chat-messages');
                const scrollAnchor = document.getElementById('scroll-anchor');
                if (chatContainer) {
                    chatContainer.scrollTop = chatContainer.scrollHeight;
                }
                if (scrollAnchor) {
                    scrollAnchor.scrollIntoView({ behavior: 'auto', block: 'end' });
                }
            }, 50);
            """
        )
    
    def enviar_mensaje(self):
        if self.mensaje.strip() != "":
            # Agregar mensaje del usuario con timestamp
            timestamp = time.strftime("%H:%M")
            self.mensajes.append({"texto": self.mensaje, "es_usuario": True, "timestamp": timestamp})
            mensaje_enviado = self.mensaje
            self.mensaje = ""
            
            # Forzar desplazamiento al fondo
            self.scroll_to_bottom()
            
            # Indicar que estamos cargando
            self.is_loading = True
            
            # Generar respuesta con Gemini
            yield
            try:
                respuesta = self._generar_respuesta_gemini(mensaje_enviado)
                # Agregar respuesta con timestamp actual
                response_timestamp = time.strftime("%H:%M")
                self.mensajes.append({"texto": respuesta, "es_usuario": False, "timestamp": response_timestamp})
                self.error_message = None
            except Exception as e:
                self.error_message = f"Error al generar respuesta: {str(e)}"
                # Agregar un mensaje de error como respuesta con timestamp
                error_timestamp = time.strftime("%H:%M")
                self.mensajes.append({"texto": f"Lo siento, ocurrió un error: {str(e)}", "es_usuario": False, "timestamp": error_timestamp})
            finally:
                self.is_loading = False
                # Forzar desplazamiento nuevamente al recibir respuesta
                self.scroll_to_bottom()
    
    def _generar_respuesta_gemini(self, mensaje: str) -> str:
        """Generar respuesta usando la API de Gemini"""
        if not self.api_key or genai is None:
            return "Por favor, configura tu API key de Gemini primero."
        
        try:
            # Asegurarse de que la API esté configurada antes de cada llamada
            genai.configure(api_key=self.api_key)
            
            # Configurar el modelo Gemini 1.5 Flash con parámetros optimizados
            model = genai.GenerativeModel(
                'gemini-1.5-flash',
                generation_config={
                    'temperature': 0.7,  # Controla la creatividad (0.0-1.0)
                    'top_p': 0.95,      # Controla la diversidad
                    'top_k': 40,        # Limita las opciones de tokens
                    'max_output_tokens': 800,  # Limita la longitud de la respuesta
                }
            )
            
            # Generar respuesta
            response = model.generate_content(mensaje)
            
            # Extraer el texto de la respuesta
            return response.text
        except Exception as e:
            # En caso de error, devolver un mensaje de error detallado
            error_msg = str(e)
            print(f"Error en Gemini API: {error_msg}")
            return f"Error al generar respuesta: {error_msg}"


def mensaje_componente(mensaje: dict) -> rx.Component:
    # Componente para mostrar un mensaje individual
    es_usuario = mensaje["es_usuario"]
    
    # Usar la hora almacenada en el mensaje o la hora actual como respaldo
    hora_mensaje = mensaje.get("timestamp", time.strftime("%H:%M"))
    
    return rx.hstack(
        # Contenedor principal del mensaje
        rx.box(
            rx.vstack(
                # Contenido del mensaje
                rx.text(
                    mensaje["texto"],
                    white_space="pre-wrap",
                    overflow_wrap="break-word",
                    width="100%",
                    color="white",
                    font_size="sm",
                    max_width="100%",  # Asegurar que el texto no se desborde
                ),
                # Hora del mensaje (abajo a la derecha)
                rx.text(
                    hora_mensaje,
                    font_size="xs",
                    color=rx.cond(es_usuario, "whiteAlpha.800", "whiteAlpha.800"),
                    align_self="flex-end",
                    margin_top="1",
                ),
                align_items="flex-start",
                spacing="0",
                width="100%",
            ),
            bg=rx.cond(es_usuario, "purple", "#000000"),  # Usuario rojo, AI púrpura
            margin_bottom="10px",
            padding="10px",
            border_radius="10px",
            max_width="80%",
            width="auto",
            overflow="hidden",
        ),
        width="100%",
        justify=rx.cond(es_usuario, "flex-end", "flex-start"),
        spacing="1",
    )


def index() -> rx.Component:
    return rx.center(
        rx.vstack(
            
            # Área de mensajes con desplazamiento automático
            rx.box(
                rx.vstack(
                    # Mensajes
                    rx.foreach(
                        ChatState.mensajes,
                        mensaje_componente
                    ),
                    # Indicador de carga
                    rx.cond(
                        ChatState.is_loading,
                        rx.spinner(color="gray", size="2"),
                        rx.text(""),
                    ),
                    # Mensaje de error
                    rx.cond(
                        ChatState.error_message,
                        rx.text(
                            ChatState.error_message,
                            color="red.500",
                            font_size="sm",
                            white_space="pre-wrap",
                            overflow_wrap="break-word",
                        ),
                        rx.text(""),
                    ),
                    # Elemento de anclaje al final para asegurar el scroll al fondo
                    rx.box(
                        height="1px", 
                        width="100%", 
                        id="chat-bottom",
                        _html="<div id='scroll-anchor' style='height:1px;width:100%;'></div>"
                    ),
                    
                    # Usamos un enfoque más robusto para el scroll automático
                    rx.box(
                        # Este componente es invisible pero ejecuta el efecto de scroll
                        on_mount=rx.call_script(
                            """
                            function scrollToBottom() {
                                const chatContainer = document.getElementById('chat-messages');
                                if (chatContainer) {
                                    chatContainer.scrollTop = chatContainer.scrollHeight;
                                }
                            }
                            scrollToBottom();
                            """
                        ),
                        # Usamos el scroll_id para forzar la re-ejecución cuando cambian los mensajes
                        key=f"scroll-effect-{ChatState.scroll_id}",
                        width="0",
                        height="0",
                        display="none",
                    ),
                    # Script mejorado para garantizar que el scroll siempre esté en la parte inferior
                    rx.script(
                        """
                        // Función para forzar el scroll al fondo
                        function forceScrollToBottom() {
                            const chatContainer = document.getElementById('chat-messages');
                            const scrollAnchor = document.getElementById('scroll-anchor');
                            
                            if (chatContainer) {
                                // Método 1: Usar scrollTop
                                chatContainer.scrollTop = chatContainer.scrollHeight;
                                
                                // Método 2: Usar scrollIntoView si existe el ancla
                                if (scrollAnchor) {
                                    scrollAnchor.scrollIntoView({ behavior: 'auto', block: 'end' });
                                }
                            }
                        }
                        
                        // Función principal para mantener el scroll al fondo
                        function setupScrollBehavior() {
                            const chatContainer = document.getElementById('chat-messages');
                            if (!chatContainer) return;
                            
                            // Forzar scroll al fondo inmediatamente
                            forceScrollToBottom();
                            
                            // Configurar un observador para detectar cambios en el contenido
                            const observer = new MutationObserver(() => {
                                // Usar setTimeout para asegurar que se ejecute después de que el DOM se actualice
                                setTimeout(forceScrollToBottom, 0);
                            });
                            
                            // Configurar el observador para detectar cualquier cambio en el contenido
                            observer.observe(chatContainer, {
                                childList: true,
                                subtree: true,
                                characterData: true,
                                attributes: true
                            });
                            
                            // También forzar el scroll al fondo cuando se redimensione la ventana
                            window.addEventListener('resize', forceScrollToBottom);
                            
                            // Forzar el scroll al fondo periódicamente para mayor seguridad
                            setInterval(forceScrollToBottom, 500);
                        }
                        
                        // Ejecutar cuando el DOM esté listo
                        if (document.readyState === 'loading') {
                            document.addEventListener('DOMContentLoaded', setupScrollBehavior);
                        } else {
                            // Si el DOM ya está cargado, ejecutar inmediatamente
                            setupScrollBehavior();
                        }
                        
                        // Ejecutar también después de un breve retraso para asegurar que todo esté cargado
                        setTimeout(setupScrollBehavior, 100);
                        setTimeout(setupScrollBehavior, 500);
                        setTimeout(setupScrollBehavior, 1000);
                        """
                    ),
                    id="chat-messages",  # ID para referencia en JavaScript
                    width="100%",
                    align_items="stretch",
                    spacing="3",
                    padding="4",
                    overflow_y="auto",
                    height="60vh",  # Mayor altura para mostrar más mensajes
                    max_height="500px",  # Altura máxima
                    scroll_behavior="smooth",  # Hacer el scroll más suave
                    position="relative",  # Posicionamiento relativo para el contenido
                    flex_grow="1",  # Permitir que crezca para llenar el espacio disponible
                    min_height="0"  # Necesario para que flex_grow funcione correctamente con scroll
                ),
                width="100%",
                overflow="hidden",  # Evitar scroll horizontal
                display="flex",
                flex_direction="column",  # Organizar mensajes verticalmente
                flex="1",  # Tomar todo el espacio disponible
                position="relative"  # Necesario para el posicionamiento correcto
            ),
            
            # Área de entrada de mensajes con estilo moderno
            rx.hstack(
                # Campo de entrada con manejo de tecla Enter
                rx.input(
                    placeholder="Message...",
                    on_change=ChatState.set_mensaje,
                    value=ChatState.mensaje,
                    flex="1",
                    padding="3",
                    border_radius="full",
                    bg="black",
                    border="none",
                    # Evento de tecla para enviar con Enter
                    on_key_down=ChatState.handle_key_press,
                ),
                # Botón de enviar (visible pero oculto en la imagen)
                rx.button(
                    "Enviar",
                    on_click=ChatState.enviar_mensaje,
                    bg="blue.500",
                    color="white",
                    padding="3",
                    border_radius="full",
                    is_disabled=rx.cond(ChatState.is_loading, True, False),
                ),
                width="100%",
                padding="3",
                spacing="3",
                bg="black",
                border_color="gray.200",
                border_bottom_radius="lg",
                margin_top="20px",
                align_items="center",
            ),
            
            width="100%",
            max_width="400px",
            bg="black",
            border_radius="2xl",
            shadow="xl",
            spacing="0",
            overflow="hidden"
        ),
        width="100%",
        height="100vh",
        bg="black",
        padding="4"
    )

app = rx.App(
    theme=app_theme,
    style=app_style,
    stylesheets=[
        "https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap",
    ],
)
app.add_page(index)
