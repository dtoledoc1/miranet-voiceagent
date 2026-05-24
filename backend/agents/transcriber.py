import asyncio
import logging
import time

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("TranscriberAgent")

class TranscriberAgent:
    def __init__(self):
        self.model = "MockModel"
        self.device = "cpu"
        logger.info("Initialized Mock Transcriber (No PyTorch/No Whisper for Render compatibility)")

    async def load(self):
        """Mock load, does nothing to save memory."""
        logger.info("Mock Whisper model initialized successfully (Render/Memory-efficient mode).")

    async def transcribe(self, audio_bytes: bytes) -> tuple[str, int]:
        """
        Mock transcription that returns empty text to prevent fake queries.
        
        Returns:
            tuple[str, int]: (transcribed_text, latency_ms)
        """
        if not audio_bytes:
            return "", 0

        start_time = time.perf_counter()
        
        # Simulate a small realistic processing delay (300ms)
        await asyncio.sleep(0.3)
        
        # Return empty string. The browser speech recognition will provide the real text.
        text = ""
        
        latency_ms = int((time.perf_counter() - start_time) * 1000)
        logger.info(f"Mock Transcription completed in {latency_ms}ms: empty text")
        return text, latency_ms
