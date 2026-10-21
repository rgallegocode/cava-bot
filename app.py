from agent import build_agent
from Gradio_UI import GradioUI

try:
    # Hugging Face asigna ZeroGPU a los Spaces de cuentas gratuitas y exige al menos una función @spaces.GPU al arrancar.
    # El LLM corre en Groq, así que esta función nunca se llama y la demo no consume GPU.
    import spaces

    @spaces.GPU
    def _zerogpu_placeholder():
        pass

except ImportError:  # en local y en CI no hace falta
    pass

GradioUI(build_agent()).launch()
