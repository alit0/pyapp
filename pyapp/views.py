import reflex as rx
from .controllers import Estado

# --- Estilos ---
COLOR_FONDO = "#f0f0f0"
COLOR_MENSAJE_USUARIO = "#4285f4"
COLOR_MENSAJE_AI = "#ffffff"
COLOR_TEXTO_USUARIO = "#ffffff"
COLOR_TEXTO_AI = "#000000"
SHADOW = "rgba(0, 0, 0, 0.05) 0px 4px 4px"
COLOR_ADJUNTO = "#e2e8f0"

# --- Componentes de la UI ---
def mensaje_componente(mensaje: dict) -> rx.Component:
    es_usuario = mensaje["es_usuario"]
    tiene_adjunto = mensaje.get("tiene_adjunto", False)
    nombre_archivo = mensaje.get("nombre_archivo", "")
    
    # Componente para mostrar el archivo adjunto si existe
    adjunto_componente = rx.cond(
        tiene_adjunto,
        rx.box(
            rx.hstack(
                rx.button(
                    rx.icon("paperclip", color="black"),
                    rx.text(
                        nombre_archivo, 
                        font_size="10px", 
                        color="black",
                        max_width="120px",
                        overflow="hidden",
                        text_overflow="ellipsis",
                        white_space="nowrap",
                    ),
                    bg=COLOR_ADJUNTO,
                    padding="4px 8px",
                    border_radius="4px",
                    margin_bottom="4px",
                ), bg=COLOR_MENSAJE_USUARIO
            ),
        ),
        rx.box(),
    )
    
    return rx.box(
        rx.box(
            rx.vstack(
                adjunto_componente,
                rx.text(
                    mensaje["texto"],
                    color=rx.cond(es_usuario, COLOR_TEXTO_USUARIO, COLOR_TEXTO_AI),
                    white_space="pre-wrap",
                    word_break="break-word",
                    overflow_wrap="break-word",
                    width="100%",
                ),
                align_items="start",
                spacing="1",
            ),
            bg=rx.cond(es_usuario, COLOR_MENSAJE_USUARIO, COLOR_MENSAJE_AI),
            padding="10px",
            border_radius=rx.cond(es_usuario,"8px 0 8px 8px", "0 8px 8px 8px"),
            box_shadow=SHADOW,
            max_width="85%",
            min_width="0",
            overflow="hidden",
        ),
        display="flex",
        justify_content=rx.cond(es_usuario, "flex-end", "flex-start"),
        margin_bottom="10px",
        width="100%",
    )

def index() -> rx.Component:
    return rx.box(
        rx.vstack(
            # Encabezado con información
            rx.box(
                rx.vstack(
                    rx.heading("Chat con Gemini", size="6", color="white"),
                    rx.text(
                        "Adjunta archivos PDF, DOCX, XLSX o TXT para analizarlos con IA",
                        color="white",
                        font_size="0.9em",
                        opacity="0.8"
                    ),
                    align_items="center",
                    spacing="2",
                ),
                bg=COLOR_MENSAJE_USUARIO,
                padding="15px",
                width="100%",
            ),
            # Área de mensajes
            rx.box(
                rx.vstack(
                    rx.foreach(Estado.mensajes, mensaje_componente),
                    align_items="stretch",
                    padding_x="20px",
                    padding_y="10px",
                    width="100%",
                ),
                id="chat-container", # ID para el scroll
                flex="1",
                overflow_y="auto",
                width="100%",
            ),
            # Spinner de carga
            rx.cond(
                Estado.cargando,
                rx.center(rx.spinner(color="blue", size="3"), padding="10px", width="100%"),
            ),
            # Mostrar archivo adjunto si existe
            rx.cond(
                Estado.mostrar_adjunto,
                rx.hstack(
                    rx.icon("paperclip", color="gray"),
                    rx.text(Estado.archivo_adjunto["name"], font_size="0.8em"),
                    rx.text(
                        Estado.tamaño_archivo_formateado,
                        font_size="0.7em",
                        color="gray"
                    ),
                    rx.spacer(),
                    rx.icon(
                        "x",
                        color="gray",
                        cursor="pointer",
                        on_click=Estado.eliminar_adjunto,
                        _hover={"color": "red"},
                    ),
                    bg=COLOR_ADJUNTO,
                    padding="8px 12px",
                    border_radius="8px",
                    margin_x="10px",
                    width="calc(100% - 20px)",
                    border="1px solid #d1d5db",
                ),
            ),
            # Área de entrada de mensajes
            rx.hstack(
                # Componente de upload oficial de Reflex
                rx.vstack(
                    rx.upload(
                        rx.button(
                            rx.icon("paperclip", size=16),
                            bg="#f9fafb",
                            color="#444444",
                            border="1px solid #ddd",
                            border_radius="8px",
                            padding="8px",
                            cursor="pointer",
                            _hover={"bg": "#f3f4f6"},
                            height="44px",
                            width="44px",
                        ),
                        id="file_upload",
                        accept={
                            "application/pdf": [".pdf"],
                            "application/vnd.openxmlformats-officedocument.wordprocessingml.document": [".docx"],
                            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": [".xlsx"],
                            "application/vnd.ms-excel": [".xls"],
                            "text/plain": [".txt"]
                        },
                        multiple=False,
                        padding="0",
                        margin="0",
                        width="44px",
                        height="44px",
                    ),
                    # Botón para procesar el archivo seleccionado (oculto si no hay archivos)
                    rx.cond(
                        rx.selected_files("file_upload"),
                        rx.button(
                            "📎 Usar archivo",
                            on_click=Estado.handle_upload(rx.upload_files("file_upload")),
                            size="1",
                            color_scheme="blue",
                            variant="soft",
                            margin_top="4px",
                            font_size="12px",
                            padding="4px 8px",
                            height="auto",
                            width="auto",
                            white_space="nowrap",
                        ),
                        rx.box(),
                    ),
                    spacing="2",
                    align_items="center",
                ),
                rx.input(
                    placeholder="Escribe un mensaje o adjunta un archivo para analizar...",
                    value=Estado.mensaje,
                    on_change=Estado.set_mensaje,
                    on_key_down=lambda key: rx.cond(key == "Enter", Estado.enviar_mensaje, None),
                    flex="1",
                    border="1px solid #ddd",
                    border_radius="8px",
                    padding="12px",
                    bg="#FFFFFF",
                    color="#090909",
                    height="44px",
                    font_size="14px",
                ),
                rx.button(
                    rx.icon("arrow-right", size=18),
                    on_click=Estado.enviar_mensaje,
                    is_disabled=Estado.cargando,
                    bg=COLOR_MENSAJE_USUARIO,
                    color="white",
                    border_radius="8px",
                    height="44px",
                    width="44px",
                    padding="0",
                    cursor="pointer",
                    _hover={"bg": "#3367d6"},
                    _disabled={"bg": "#9ca3af", "cursor": "not-allowed"},
                ),
                width="100%",
                padding="15px",
                bg="#FFFFFF",
                border_top="1px solid #e5e7eb",
                gap="12px",
                align_items="center",
            ),
            height="100vh",
            width="100%",
            spacing="0",
            bg=COLOR_FONDO,
        ),
    )