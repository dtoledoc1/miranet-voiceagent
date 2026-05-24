import asyncio
import logging
import time
import numpy as np
import torch
import whisper
from backend.config import settings

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("TranscriberAgent")

class TranscriberAgent:
    def __init__(self):
        self.model = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        
        # Configure PyTorch CPU thread count to avoid high-CPU locks or memory bottlenecks
        torch.set_num_threads(settings.TORCH_NUM_THREADS)
        logger.info(f"Initialized Transcriber. PyTorch thread count set to: {settings.TORCH_NUM_THREADS}. Device: {self.device}")

    async def load(self):
        """Asynchronously load the Whisper model on server startup to avoid first-request delay."""
        try:
            logger.info(f"Loading Whisper model '{settings.WHISPER_MODEL_NAME}' from download root '{settings.WHISPER_DOWNLOAD_ROOT}'...")
            
            # Execute synchronous whisper load inside a thread pool to avoid blocking the event loop
            def _load():
                return whisper.load_model(
                    name=settings.WHISPER_MODEL_NAME,
                    device=self.device,
                    download_root=settings.WHISPER_DOWNLOAD_ROOT
                )
                
            self.model = await asyncio.to_thread(_load)
            logger.info("Whisper model loaded successfully and is ready.")
        except Exception as e:
            logger.error(f"Error loading Whisper model: {e}", exc_info=True)
            raise

    async def transcribe(self, audio_bytes: bytes) -> tuple[str, int]:
        """
        Transcribe raw PCM 16-bit mono 16kHz audio bytes.
        
        Returns:
            tuple[str, int]: (transcribed_text, latency_ms)
        """
        if not self.model:
            logger.error("Whisper model is not loaded. Call load() first.")
            return "", 0

        if not audio_bytes:
            return "", 0

        start_time = time.perf_counter()
        
        try:
            # Handle potential uneven byte array length
            if len(audio_bytes) % 2 != 0:
                audio_bytes = audio_bytes[:-1]

            # Convert 16-bit PCM bytes to numpy float32 array normalized to [-1.0, 1.0]
            audio_np = np.frombuffer(audio_bytes, dtype=np.int16).astype(np.float32) / 32768.0

            # Run whisper transcription in thread pool to keep loop non-blocking
            def _run_transcribe():
                # fp16=False is safer for CPU and prevents warnings.
                # Suppress verbose terminal prints by setting verbose=None
                return self.model.transcribe(audio_np, fp16=(self.device == "cuda"), verbose=None)

            result = await asyncio.to_thread(_run_transcribe)
            text = result.get("text", "").strip()
            
            latency_ms = int((time.perf_counter() - start_time) * 1000)
            logger.info(f"Transcription completed in {latency_ms}ms: '{text}'")
            return text, latency_ms
            
        except Exception as e:
            latency_ms = int((time.perf_counter() - start_time) * 1000)
            logger.error(f"Error during transcription: {e}", exc_info=True)
            return "", latency_ms
