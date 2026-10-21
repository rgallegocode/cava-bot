from agent import build_agent
from Gradio_UI import GradioUI

try:
    # Hugging Face assigns ZeroGPU to Spaces of free accounts and requires at least one @spaces.GPU function at startup.
    # The LLM runs on Groq, so this function is never called and the demo uses no GPU time.
    import spaces

    @spaces.GPU
    def _zerogpu_placeholder():
        pass

except ImportError:  # not needed locally or in CI
    pass

GradioUI(build_agent()).launch()
