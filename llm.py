# llm.py
import ollama

class LLM:
    def __init__(self, model: str = "gpt-oss:120b", ollama_url: str = None):
        """Initialize LLM with Ollama model.
        
        Args:
            model: The Ollama model to use
            ollama_url: Optional Ollama server URL (e.g., "https://ollama:11434")
        """
        self.model = model
        # reasoning not relevant for Ollama, so always False
        self.should_reason = False
        
        # Create client with custom host if provided
        if ollama_url:
            self.client = ollama.Client(host=ollama_url)
        else:
            self.client = ollama.Client()  # Uses default localhost:11434

    def action(self, messages, temperature: float = 0.0, **kwargs):
        """
        Send messages to Ollama for chat completion.
        Ignores any unsupported kwargs like 'reasoning'.
        """
        try:
            response = self.client.chat(
                model=self.model,
                messages=messages,
                options={
                    "temperature": temperature,
                    "num_predict": -1  # Allow unlimited tokens
                },
                stream=False,  # Explicitly disable streaming
                tools=None  # Explicitly disable tool calling
            )
            return response["message"]["content"]
        except Exception as e:
            # If there's an error, try without any extra options
            print(f"Warning: Ollama request failed with options, retrying... Error: {e}")
            try:
                response = self.client.chat(
                    model=self.model,
                    messages=messages,
                    tools=None  # Try with just disabling tools
                )
                return response["message"]["content"]
            except Exception as e2:
                # Last resort - minimal request
                print(f"Warning: Retrying with minimal options... Error: {e2}")
                response = self.client.chat(
                    model=self.model,
                    messages=messages
                )
                return response["message"]["content"]

    def prompt(self, prompt: str, temperature: float = 0.0, **kwargs):
        """
        Send a simple prompt to Ollama.
        Ignores any unsupported kwargs like 'reasoning'.
        """
        try:
            response = self.client.chat(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                options={"temperature": temperature},
                stream=False  # Explicitly disable streaming
            )
            return response["message"]["content"]
        except Exception as e:
            # If there's an error, try without any extra options
            print(f"Warning: Ollama request failed with options, retrying... Error: {e}")
            response = self.client.chat(
                model=self.model,
                messages=[{"role": "user", "content": prompt}]
            )
            return response["message"]["content"]