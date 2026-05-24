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
        self.counter = 0
        self.mock_transcriptions = [
            "Hola, buenas, mi internet está súper lento desde hace dos horas.",
            "Se cayó el internet por completo, mis vecinos tampoco tienen señal en la zona.",
            "Quería hacer una consulta sobre mi recibo de pago por favor.",
            "El módem tiene una luz roja parpadeando y no puedo conectarme.",
            "Hola, mi señal de internet se corta a cada rato."
        ]
        logger.info("Initialized Mock Transcriber (No PyTorch/No Whisper for Render compatibility)")

    async def load(self):
        """Mock load, does nothing to save memory."""
        logger.info("Mock Whisper model initialized successfully (Render/Memory-efficient mode).")

    async def transcribe(self, audio_bytes: bytes) -> tuple[str, int]:
        """
        Mock transcription that cycles through typical user complaints.
        
        Returns:
            tuple[str, int]: (transcribed_text, latency_ms)
        """
        if not audio_bytes:
            return "", 0

        start_time = time.perf_counter()
        
        # Simulate a small realistic processing delay (300ms)
        await asyncio.sleep(0.3)
        
        # Cycle through typical complaints to make the demo interactive
        text = self.mock_transcriptions[self.counter % len(self.mock_transcriptions)]
        self.counter += 1
        
        latency_ms = int((time.perf_counter() - start_time) * 1000)
        logger.info(f"Mock Transcription completed in {latency_ms}ms: '{text}'")
        return text, latency_ms
