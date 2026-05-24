import json
import time
import logging
import httpx
from backend.config import settings

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ClassifierAgent")

class ClassifierAgent:
    def __init__(self):
        self.base_url = settings.OLLAMA_BASE_URL
        self.model = settings.OLLAMA_MODEL
        self.client = httpx.AsyncClient(timeout=30.0)

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()

    async def classify(self, text: str) -> tuple[dict, int]:
        """
        Classify transcription text using Ollama (Mistral 7B).
        
        Returns:
            tuple[dict, int]: (classification_result, latency_ms)
        """
        if not text:
            return {"intent": "unknown", "sentiment": "neutral"}, 0

        start_time = time.perf_counter()
        
        system_prompt = (
            "You are a classification agent for Miranet VoiceAgent.\n"
            "Analyze the following user speech text and return ONLY a valid JSON object.\n"
            "Do NOT include any markdown code blocks, explanation, or conversational filler.\n"
            "The JSON object must have exactly these keys:\n"
            "  - 'intent': (string, e.g., 'greeting', 'billing', 'technical_support', 'general_query', 'cancel_service', 'unknown')\n"
            "  - 'sentiment': (string, e.g., 'positive', 'neutral', 'negative', 'frustrated')\n"
            "Example output:\n"
            '{"intent": "greeting", "sentiment": "positive"}'
        )

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": text}
            ],
            "stream": False,
            "format": "json",  # Instruct Ollama to output valid JSON
            "options": {
                "temperature": 0.0,
                "num_predict": 64  # Keep it short to minimize latency
            }
        }

        try:
            logger.info(f"Sending classification request to Ollama: '{text}'")
            response = await self.client.post(
                f"{self.base_url}/api/chat",
                json=payload
            )
            response.raise_for_status()
            
            response_data = response.json()
            content = response_data.get("message", {}).get("content", "").strip()
            
            # Parse the JSON response
            classification = json.loads(content)
            
            # Clean and ensure default keys are present
            result = {
                "intent": classification.get("intent", "unknown"),
                "sentiment": classification.get("sentiment", "neutral")
            }
            
            latency_ms = int((time.perf_counter() - start_time) * 1000)
            logger.info(f"Classification completed in {latency_ms}ms: {result}")
            return result, latency_ms

        except (httpx.HTTPError, json.JSONDecodeError, KeyError) as e:
            latency_ms = int((time.perf_counter() - start_time) * 1000)
            logger.error(f"Error during classification: {e}")
            # Fallback values
            return {"intent": "unknown", "sentiment": "neutral"}, latency_ms
