import reflex as rx
from .controllers import Estado

# --- Estilos ---
COLOR_FONDO = "#f0f0f0"
COLOR_MENSAJE_USUARIO = "#4285f4"
COLOR_MENSAJE_AI = "#ffffff"
COLOR_TEXTO_USUARIO = "#ffffff"
COLOR_TEXTO_AI = "#000000"
SHADOW = "rgba(0, 0, 0, 0.05) 0px 4px 4px"

# --- Componentes de la UI ---
def mensaje_componente(mensaje: dict) -> rx.Component:
    es_usuario = mensaje["es_usuario"]
    return rx.box(
        rx.box(
            rx.text(
                mensaje["texto"],
                color=rx.cond(es_usuario, COLOR_TEXTO_USUARIO, COLOR_TEXTO_AI),
                white_space="pre-wrap",
            ),
            bg=rx.cond(es_usuario, COLOR_MENSAJE_USUARIO, COLOR_MENSAJE_AI),
            padding="10px",
            border_radius=rx.cond(es_usuario,"8px 0 8px 8px", "0 8px 8px 8px"),
            box_shadow=SHADOW,
            max_width="85%",
        ),
        display="flex",
        justify_content=rx.cond(es_usuario, "flex-end", "flex-start"),
        margin_bottom="10px",
        width="100%",
    )

def index() -> rx.Component:
    return rx.box(
        rx.vstack(
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
            # Área de entrada de mensajes
            rx.hstack(
                rx.input(
                    placeholder="Escribe un mensaje...",
                    value=Estado.mensaje,
                    on_change=Estado.set_mensaje,
                    on_key_down=lambda key: rx.cond(key == "Enter", Estado.enviar_mensaje, None),
                    flex="1",
                    border="1px solid #ddd",
                    border_radius="md",
                    padding="4px",
                    bg="white",
                    color="#090909"
                ),
                rx.button(
                    rx.icon("arrow-right"),
                    on_click=Estado.enviar_mensaje,
                    is_disabled=Estado.cargando,
                    bg=COLOR_MENSAJE_USUARIO,
                    color="white",
                    border_radius="md",
                    height="100%",
                ),
                width="100%",
                padding="10px",
                bg="white",
                border_top="1px solid #f0f0f0",
            ),
            height="100vh",
            width="100%",
            spacing="0",
            bg=COLOR_FONDO,
        ),
    )
