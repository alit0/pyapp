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
                    rx.text(nombre_archivo, font_size="10px", color="black"),
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
                ),
                align_items="start",
                spacing="1",
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
            # Mostrar archivo adjunto si existe
            rx.cond(
                Estado.mostrar_adjunto,
                rx.hstack(
                    rx.icon("paperclip", color="gray"),
                    rx.text(Estado.archivo_adjunto["name"], font_size="0.8em"),
                    rx.spacer(),
                    rx.icon(
                        "x",
                        color="gray",
                        cursor="pointer",
                        on_click=Estado.eliminar_adjunto,
                        _hover={"color": "red"},
                    ),
                    bg=COLOR_ADJUNTO,
                    padding="4px 8px",
                    border_radius="4px",
                    margin_x="10px",
                    width="100%",
                ),
            ),
            # Área de entrada de mensajes
            rx.hstack(
                # Input de tipo file para adjuntar archivos
                rx.html("""
                <label style="cursor: pointer; display: flex; align-items: center; justify-content: center; height: 100%; padding: 4px 4px; border-radius: 8px; color: #444444;">
                    <svg xmlns="http://www.w3.org/2000/svg" width="25" height="25" fill="currentColor" class="bi bi-paperclip" viewBox="0 0 16 16" style="font-size: 16px">
                        <path d="M4.5 3a2.5 2.5 0 0 1 5 0v9a1.5 1.5 0 0 1-3 0V5a.5.5 0 0 1 1 0v7a.5.5 0 0 0 1 0V3a1.5 1.5 0 1 0-3 0v9a2.5 2.5 0 0 0 5 0V5a.5.5 0 0 1 1 0v7a3.5 3.5 0 1 1-7 0V3z"/>
                    </svg>
                    <input 
                        type="file" 
                        id="file-upload" 
                        style="display: none;" 
                        onchange="window.dispatchEvent(new CustomEvent('__reflex_file_selected', {detail: {files: this.files}}));"
                    />
                </label>
                """),
                # Script para manejar la selección de archivos
                rx.script("""
                window.addEventListener('__reflex_file_selected', function(e) {
                    const file = e.detail.files[0];
                    if (!file) return;
                    
                    const reader = new FileReader();
                    reader.onload = function(event) {
                        const fileContent = event.target.result;
                        window._reflex.addEvent({
                            name: "adjuntar_archivo",
                            payload: {
                                name: file.name,
                                type: file.type,
                                size: file.size,
                                content: fileContent
                            }
                        });
                    };
                    reader.readAsDataURL(file);
                });
                """),
                rx.input(
                    placeholder="Escribe un mensaje...",
                    value=Estado.mensaje,
                    on_change=Estado.set_mensaje,
                    on_key_down=lambda key: rx.cond(key == "Enter", Estado.enviar_mensaje, None),
                    flex="1",
                    border="1px solid #ddd",
                    border_radius="8px",
                    padding="4px",
                    bg="#FFFFFF",
                    color="#090909"
                ),
                rx.button(
                    rx.icon("arrow-right"),
                    on_click=Estado.enviar_mensaje,
                    is_disabled=Estado.cargando & ~Estado.mostrar_adjunto,
                    bg=COLOR_MENSAJE_USUARIO,
                    color="white",
                    border_radius="8px",
                    height="100%",
                ),
                width="100%",
                padding="10px",
                bg="#FFFFFF",
                border_top="1px solid #f0f0f0",
            ),
            height="100vh",
            width="100%",
            spacing="0",
            bg=COLOR_FONDO,
        ),
    )
