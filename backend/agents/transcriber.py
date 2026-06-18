import time
import logging
import torch
import numpy as np
import whisper
import asyncio
from backend.config import settings

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("TranscriberAgent")

class TranscriberAgent:
    def __init__(self):
        self.model_name = settings.WHISPER_MODEL_NAME
        self.download_root = settings.WHISPER_DOWNLOAD_ROOT
        self.device = "cpu"
        self.model = None
        
        # Optimize PyTorch CPU execution
        torch.set_num_threads(settings.TORCH_NUM_THREADS)
        logger.info(f"Initialized local Whisper Transcriber using torch threads: {settings.TORCH_NUM_THREADS}")

    async def load(self):
        """Load the local Whisper model in a thread pool to avoid blocking the event loop."""
        def _load_model():
            logger.info(f"Loading local Whisper model '{self.model_name}' from {self.download_root}...")
            return whisper.load_model(self.model_name, download_root=self.download_root, device=self.device)

        try:
            self.model = await asyncio.to_thread(_load_model)
            logger.info("Local Whisper model loaded successfully.")
        except Exception as e:
            logger.error(f"Error loading local Whisper model: {e}")
            raise

    async def transcribe(self, audio_bytes: bytes) -> tuple[str, int]:
        """
        Transcribe raw PCM 16-bit mono 16kHz audio bytes using the local Whisper model.
        
        Returns:
            tuple[str, int]: (transcribed_text, latency_ms)
        """
        if not audio_bytes or self.model is None:
            return "", 0

        start_time = time.perf_counter()
        
        try:
            # Handle potential uneven byte array length
            if len(audio_bytes) % 2 != 0:
                audio_bytes = audio_bytes[:-1]

            # Convert 16-bit signed PCM audio bytes to float32 NumPy array normalized to [-1.0, 1.0]
            audio_np = np.frombuffer(audio_bytes, dtype=np.int16).astype(np.float32) / 32768.0

            # Run transcription in a thread pool to prevent blocking the async event loop
            def _run_transcription():
                result = self.model.transcribe(
                    audio_np,
                    language="es",
                    fp16=False,  # Float16 is not supported/recommended on CPU
                    temperature=0.0  # Deterministic transcription
                )
                return result.get("text", "").strip()

            text = await asyncio.to_thread(_run_transcription)
            
            latency_ms = int((time.perf_counter() - start_time) * 1000)
            logger.info(f"Local Whisper STT completed in {latency_ms}ms: '{text}'")
            return text, latency_ms
            
        except Exception as e:
            latency_ms = int((time.perf_counter() - start_time) * 1000)
            logger.error(f"Error during local Whisper STT transcription: {e}")
            return "", latency_ms
