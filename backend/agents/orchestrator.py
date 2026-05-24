import logging
from backend.db.database import db
from backend.agents.transcriber import TranscriberAgent
from backend.agents.classifier import ClassifierAgent
from backend.agents.responder import ResponderAgent
from backend.agents.network_monitor import NetworkMonitorAgent

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("OrchestratorAgent")

class OrchestratorAgent:
    def __init__(
        self,
        transcriber: TranscriberAgent,
        classifier: ClassifierAgent,
        responder: ResponderAgent
    ):
        self.transcriber = transcriber
        self.classifier = classifier
        self.responder = responder
        # Store active session contexts in memory
        self.active_sessions = {}

    async def start_session(self, session_id: str):
        """Initialize resources and database records for a new session."""
        logger.info(f"Starting session: {session_id}")
        
        # Log to DB
        await db.create_conversation(session_id)
        
        # Setup session context
        self.active_sessions[session_id] = {
            "audio_buffer": bytearray(),
            "sequence_counter": 0,
            "history": [],
            "network_monitor": NetworkMonitorAgent()
        }

    async def append_audio_chunk(
        self,
        session_id: str,
        chunk: bytes,
        sequence_id: int | None = None
    ) -> dict:
        """
        Append incoming raw audio bytes to the session buffer.
        
        Returns:
            dict: Real-time network streaming diagnostics
        """
        session = self.active_sessions.get(session_id)
        if not session:
            raise RuntimeError(f"Session {session_id} is not initialized.")

        # Append to buffer
        session["audio_buffer"].extend(chunk)

        # Log network packet to compute jitter/loss/bandwidth
        net_monitor: NetworkMonitorAgent = session["network_monitor"]
        metrics = net_monitor.record_packet(len(chunk), sequence_id)
        
        return metrics

    async def process_audio_segment(self, session_id: str) -> dict:
        """
        Trigger the processing cascade:
        1. Whisper transcription of accumulated audio.
        2. Ollama intent & sentiment classification.
        3. Ollama contextual text response generation.
        4. DB persistence.
        
        Returns:
            dict: The complete voice transaction metadata and response text.
        """
        session = self.active_sessions.get(session_id)
        if not session:
            raise RuntimeError(f"Session {session_id} is not initialized.")

        audio_bytes = bytes(session["audio_buffer"])
        
        # Reset the audio buffer immediately to prepare for the next user utterance
        session["audio_buffer"] = bytearray()
        
        if not audio_bytes or len(audio_bytes) < 3200:  # less than 100ms of audio
            return {
                "transcription": "",
                "response": "No he recibido suficiente audio. ¿Podrías hablar más fuerte?",
                "intent": "unknown",
                "sentiment": "neutral",
                "latencies": {"transcription": 0, "classification": 0, "responder": 0}
            }

        # Increment sequence counter for this session
        session["sequence_counter"] += 1
        sequence_num = session["sequence_counter"]

        logger.info(f"Processing audio segment for {session_id} (seq: {sequence_num}, size: {len(audio_bytes)} bytes)")

        # 1. Transcribe
        transcription, t_latency = await self.transcriber.transcribe(audio_bytes)
        
        if not transcription.strip():
            logger.info("Transcription returned empty text.")
            return {
                "transcription": "",
                "response": "No te he escuchado. ¿Podrías repetir?",
                "intent": "unknown",
                "sentiment": "neutral",
                "latencies": {"transcription": t_latency, "classification": 0, "responder": 0}
            }

        # 2. Classify & Respond in a single call (bypassing old ClassifierAgent to save latency)
        c_latency = 0
        result_json, r_latency = await self.responder.generate_response(
            text=transcription,
            history=session["history"]
        )
        
        intent = result_json.get("nivel_asignado", "bajo")
        sentiment = f"{result_json.get('diagnostico_causa_raiz', 'N/A')} ({result_json.get('porcentaje_confianza', '0%')})"
        response = result_json.get("respuesta_cliente", "...")

        # Update Session History
        session["history"].append({"role": "user", "content": transcription})
        session["history"].append({"role": "assistant", "content": response})

        # 4. Save to Database asynchronously
        await db.log_voice_interaction(
            session_id=session_id,
            sequence_number=sequence_num,
            audio_size_bytes=len(audio_bytes),
            transcription=transcription,
            classification_intent=intent,
            classification_sentiment=sentiment,
            response_text=response,
            transcription_latency_ms=t_latency,
            classification_latency_ms=c_latency,
            response_latency_ms=r_latency
        )

        # Log current network summary stats to database
        net_monitor: NetworkMonitorAgent = session["network_monitor"]
        summary = net_monitor.get_summary()
        await db.log_network_metrics(
            session_id=session_id,
            latency_ms=int(summary["avg_jitter_ms"]),  # average jitter as nominal network lag
            packet_loss_rate=summary["packet_loss_rate"],
            jitter_ms=int(summary["avg_jitter_ms"]),
            bandwidth_kbps=summary["avg_bandwidth_kbps"]
        )

        return {
            "transcription": transcription,
            "response": response,
            "intent": intent,
            "sentiment": sentiment,
            "latencies": {
                "transcription": t_latency,
                "classification": c_latency,
                "responder": r_latency
            }
        }

    async def process_text_segment(self, session_id: str, transcription: str) -> dict:
        """
        Process a text transcription sent directly from the client (browser speech recognition).
        Bypasses local Whisper to save memory and CPU.
        """
        session = self.active_sessions.get(session_id)
        if not session:
            raise RuntimeError(f"Session {session_id} is not initialized.")

        audio_bytes = bytes(session["audio_buffer"])
        # Clear buffer
        session["audio_buffer"] = bytearray()
        
        # Audio size is either the buffer size or default 16000 bytes
        audio_size = len(audio_bytes) if audio_bytes else 16000
        
        # Increment sequence counter
        session["sequence_counter"] += 1
        sequence_num = session["sequence_counter"]

        logger.info(f"Processing text segment for {session_id} (seq: {sequence_num}, text: '{transcription}')")

        t_latency = 0
        c_latency = 0

        # Respond (Ollama or Hybrid Matcher)
        result_json, r_latency = await self.responder.generate_response(
            text=transcription,
            history=session["history"]
        )
        
        intent = result_json.get("nivel_asignado", "bajo")
        sentiment = f"{result_json.get('diagnostico_causa_raiz', 'N/A')} ({result_json.get('porcentaje_confianza', '0%')})"
        response = result_json.get("respuesta_cliente", "...")

        # Update Session History
        session["history"].append({"role": "user", "content": transcription})
        session["history"].append({"role": "assistant", "content": response})

        # Save to Database asynchronously
        await db.log_voice_interaction(
            session_id=session_id,
            sequence_number=sequence_num,
            audio_size_bytes=audio_size,
            transcription=transcription,
            classification_intent=intent,
            classification_sentiment=sentiment,
            response_text=response,
            transcription_latency_ms=t_latency,
            classification_latency_ms=c_latency,
            response_latency_ms=r_latency
        )

        # Log current network summary stats to database
        net_monitor: NetworkMonitorAgent = session["network_monitor"]
        summary = net_monitor.get_summary()
        await db.log_network_metrics(
            session_id=session_id,
            latency_ms=int(summary["avg_jitter_ms"]),
            packet_loss_rate=summary["packet_loss_rate"],
            jitter_ms=int(summary["avg_jitter_ms"]),
            bandwidth_kbps=summary["avg_bandwidth_kbps"]
        )

        return {
            "transcription": transcription,
            "response": response,
            "intent": intent,
            "sentiment": sentiment,
            "latencies": {
                "transcription": t_latency,
                "classification": c_latency,
                "responder": r_latency
            }
        }

    async def end_session(self, session_id: str) -> dict:
        """Log final network diagnostics and release session context."""
        session = self.active_sessions.pop(session_id, None)
        if not session:
            return {}

        net_monitor: NetworkMonitorAgent = session["network_monitor"]
        summary = net_monitor.get_summary()
        logger.info(f"Session {session_id} ended. Final network summary: {summary}")
        
        return summary
