import ollama
import google.generativeai as genai
import os
import time
from google.api_core import exceptions

class LLM:
    def __init__(self, model: str = "gpt-oss:120b", ollama_url: str = None, gemini: bool = False, api_key: str = None):
        """Initialize LLM with Ollama or Gemini model.
        
        Args:
            model: The Ollama model to use
            ollama_url: Optional Ollama server URL (e.g., "https://ollama:11434")
            gemini: Whether to use the Gemini API
            api_key: The Gemini API key
        """
        self.use_gemini = gemini
        self.model = model
        self.should_reason = False

        if self.use_gemini:
            print("Using Gemini API")
            self.model = "gemini-2.5-flash"
            if not api_key:
                raise ValueError("Gemini API key is required.")
            
            genai.configure(api_key=api_key)
            self.client = genai.GenerativeModel(self.model)
            self.last_gemini_call = 0
        else:
            print("Using Ollama API")
            # reasoning not relevant for Ollama, so always False
            self.should_reason = False
            
            # Create client with custom host if provided
            if ollama_url:
                self.client = ollama.Client(host=ollama_url)
            else:
                self.client = ollama.Client()  # Uses default localhost:11434

    def _gemini_request_wrapper(self, request_func, *args, **kwargs):
        """Wrapper for Gemini requests to handle rate limiting and retries."""
        # Rate limiting: 10 requests per minute (6 seconds between calls)
        time_since_last_call = time.time() - self.last_gemini_call
        if time_since_last_call < 6:
            time.sleep(6 - time_since_last_call)
        
        self.last_gemini_call = time.time()
        
        try:
            return request_func(*args, **kwargs)
        except exceptions.ResourceExhausted as e:
            print("Rate limit exceeded (429). Waiting for 60 seconds before retrying...")
            time.sleep(60)
            self.last_gemini_call = time.time()
            return request_func(*args, **kwargs)

    def action(self, messages, temperature: float = 0.0, **kwargs):
        """
        Send messages to the configured LLM for chat completion.
        """
        if self.use_gemini:
            # Gemini uses a different message format
            gemini_messages = []
            for msg in messages:
                role = "user" if msg["role"] == "user" else "model"
                gemini_messages.append({"role": role, "parts": [msg["content"]]})
            
            response = self._gemini_request_wrapper(
                self.client.generate_content,
                gemini_messages,
                generation_config=genai.types.GenerationConfig(
                    temperature=temperature
                )
            )
            if not response.candidates or response.candidates[0].finish_reason == 'SAFETY':
                print(f"Warning: Gemini response was blocked. Finish reason: {response.candidates[0].finish_reason if response.candidates else 'N/A'}")
                if response.candidates:
                    print(f"Safety ratings: {response.candidates[0].safety_ratings}")
                return ""
            return response.text
        else:
            try:
                response = self.client.chat(
                    model=self.model,
                    messages=messages,
                    options={
                        "temperature": temperature,
                        "num_predict": -1  # Allow unlimited tokens
                    },
                    stream=False  # Explicitly disable streaming
                )
                return response["message"]["content"]
            except Exception as e:
                # If there's an error, try without any extra options
                print(f"Warning: Ollama request failed with options, retrying... Error: {e}")
                try:
                    response = self.client.chat(
                        model=self.model,
                        messages=messages
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
        Send a simple prompt to the configured LLM.
        """
        if self.use_gemini:
            response = self._gemini_request_wrapper(
                self.client.generate_content,
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=temperature
                )
            )
            if not response.candidates or response.candidates[0].finish_reason == 'SAFETY':
                print(f"Warning: Gemini response was blocked. Finish reason: {response.candidates[0].finish_reason if response.candidates else 'N/A'}")
                if response.candidates:
                    print(f"Safety ratings: {response.candidates[0].safety_ratings}")
                return ""
            return response.text
        else:
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
