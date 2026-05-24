import io
import wave
import asyncio
import logging
import time
import speech_recognition as sr

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("TranscriberAgent")

class TranscriberAgent:
    def __init__(self):
        self.model = "GoogleSpeechAPI"
        self.device = "cloud"
        self.recognizer = sr.Recognizer()
        logger.info("Initialized Google Speech-to-Text Transcriber (Memory-free for Render)")

    async def load(self):
        """No model to load locally, API is online."""
        logger.info("Google Speech-to-Text Transcriber is ready.")

    async def transcribe(self, audio_bytes: bytes) -> tuple[str, int]:
        """
        Transcribe raw PCM 16-bit mono 16kHz audio bytes using Google's free STT API.
        
        Returns:
            tuple[str, int]: (transcribed_text, latency_ms)
        """
        if not audio_bytes:
            return "", 0

        start_time = time.perf_counter()
        
        try:
            # Handle potential uneven byte array length
            if len(audio_bytes) % 2 != 0:
                audio_bytes = audio_bytes[:-1]

            # Run STT in thread executor to keep event loop non-blocking
            def _run_google_stt():
                # 1. Package PCM bytes into a WAV container in memory
                wav_io = io.BytesIO()
                with wave.open(wav_io, 'wb') as wav_file:
                    wav_file.setnchannels(1)
                    wav_file.setsampwidth(2) # 16-bit PCM
                    wav_file.setframerate(16000) # 16kHz
                    wav_file.writeframes(audio_bytes)
                
                wav_io.seek(0)
                
                # 2. Load WAV into SpeechRecognition AudioFile
                with sr.AudioFile(wav_io) as source:
                    audio_data = self.recognizer.record(source)
                
                # 3. Transcribe using Google's public endpoint
                return self.recognizer.recognize_google(audio_data, language="es-ES")

            text = await asyncio.to_thread(_run_google_stt)
            text = text.strip() if text else ""
            
            latency_ms = int((time.perf_counter() - start_time) * 1000)
            logger.info(f"Google STT completed in {latency_ms}ms: '{text}'")
            return text, latency_ms
            
        except sr.UnknownValueError:
            latency_ms = int((time.perf_counter() - start_time) * 1000)
            logger.info(f"Google STT completed in {latency_ms}ms: Speech unintelligible (empty)")
            return "", latency_ms
        except Exception as e:
            latency_ms = int((time.perf_counter() - start_time) * 1000)
            logger.error(f"Error during Google STT transcription: {e}")
            return "", latency_ms
