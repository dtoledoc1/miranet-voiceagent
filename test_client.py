import asyncio
import json
import logging
import numpy as np
import websockets

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("TestVoiceClient")

async def run_voice_client():
    uri = "ws://localhost:8000/ws/voice?session_id=test_voice_session"
    logger.info(f"Connecting to VoiceAgent server at {uri}...")

    try:
        async with websockets.connect(uri) as websocket:
            logger.info("Connected to WebSocket. Generating synthetic voice audio data...")

            # Create 3 seconds of synthetic audio (e.g., sine wave representing voice amplitude)
            sample_rate = 16000
            duration = 3.0
            t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
            # Create a 440Hz tone
            audio_signal = np.sin(2 * np.pi * 440 * t)
            # Scale to 16-bit integer range
            audio_pcm = (audio_signal * 32767).astype(np.int16)
            audio_bytes = audio_pcm.tobytes()

            # We will send the audio in chunks of 3200 bytes (100ms of audio)
            chunk_size = 3200  # 16000 samples/sec * 2 bytes/sample * 0.1 sec = 3200 bytes
            total_chunks = len(audio_bytes) // chunk_size

            logger.info(f"Streaming {total_chunks} audio packets (100ms each) in real-time...")
            
            for i in range(total_chunks):
                start_idx = i * chunk_size
                end_idx = start_idx + chunk_size
                chunk = audio_bytes[start_idx:end_idx]

                # Send binary packet
                await websocket.send(chunk)
                
                # Receive real-time network status message from server
                recv_msg = await websocket.recv()
                try:
                    status = json.loads(recv_msg)
                    if status.get("type") == "network_status":
                        metrics = status.get("metrics", {})
                        logger.info(
                            f"Packet {i+1}/{total_chunks} sent. Server report -> "
                            f"Latency: {metrics.get('latency_ms')}ms, "
                            f"Jitter: {metrics.get('jitter_ms')}ms, "
                            f"Loss Rate: {metrics.get('packet_loss_rate')*100}%, "
                            f"Bandwidth: {metrics.get('bandwidth_kbps')} kbps"
                        )
                except json.JSONDecodeError:
                    logger.warning(f"Unexpected response payload: {recv_msg}")

                # Wait 100ms to simulate real voice stream interval
                await asyncio.sleep(0.1)

            # Once streaming is complete, declare End of Speech (EOS)
            logger.info("Streaming completed. Sending 'end_of_speech' control signal...")
            control_msg = {"type": "end_of_speech"}
            await websocket.send(json.dumps(control_msg))

            # Await processing outcome
            logger.info("Waiting for agent transcription and response...")
            response_payload = await websocket.recv()
            try:
                result = json.loads(response_payload)
                if result.get("type") == "agent_response":
                    logger.info("=== VOICE TRANSACTION COMPLETE ===")
                    logger.info(f"User transcription: '{result.get('transcription')}'")
                    logger.info(f"Classified Intent: {result.get('intent')}")
                    logger.info(f"Classified Sentiment: {result.get('sentiment')}")
                    logger.info(f"Agent Vocal Response: '{result.get('response')}'")
                    
                    latencies = result.get("latencies", {})
                    logger.info("Latencies:")
                    logger.info(f"  - Transcription: {latencies.get('transcription')} ms")
                    logger.info(f"  - Classification: {latencies.get('classification')} ms")
                    logger.info(f"  - Response Gen: {latencies.get('responder')} ms")
                    logger.info("==================================")
                else:
                    logger.warning(f"Unexpected response type: {result}")
            except json.JSONDecodeError:
                logger.error(f"Failed to parse final server response: {response_payload}")

    except Exception as e:
        logger.error(f"Client error: {e}", exc_info=True)

if __name__ == "__main__":
    asyncio.run(run_voice_client())
