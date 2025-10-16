import ollama

class LLM:
    def __init__(self, model: str = "mistral:latest"):
        """Initialize LLM with Ollama model."""
        self.model = model
        # reasoning not relevant for Ollama, so always False
        self.should_reason = False

    def action(self, messages, temperature: float = 0.0, **kwargs):
        """
        Ollama doesn't use OpenAI-style 'messages' natively, but we can
        format them into a single prompt.
        """
        # flatten chat history
        prompt = "\n".join(
            f"{m['role'].capitalize()}: {m['content']}" for m in messages
        )

        response = ollama.chat(
            model=self.model,
            messages=messages,  # Ollama’s Python API *does* accept role/content style
            options={"temperature": temperature},
        )
        return response["message"]["content"]

    def prompt(self, prompt: str, temperature: float = 0.0, **kwargs):
        response = ollama.chat(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            options={"temperature": temperature},
        )
        return response["message"]["content"]

    