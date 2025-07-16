import reflex as rx
from .views import index
from .controllers import Estado

# --- App ---
app = rx.App()
app.add_page(index, title="Chat con Gemini")