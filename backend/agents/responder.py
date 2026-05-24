import time
import logging
import httpx
import json
from backend.config import settings

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ResponderAgent")

class ResponderAgent:
    def __init__(self):
        self.base_url = settings.OLLAMA_BASE_URL
        self.model = settings.OLLAMA_MODEL
        self.client = httpx.AsyncClient(timeout=60.0)

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()

    async def generate_response(
        self,
        text: str,
        history: list[dict] = None
    ) -> tuple[dict, int]:
        """
        Generate a structured response (intent classification, diagnostic, confidence, spoken response)
        using a single optimized Ollama LLM query to minimize real-time voice latency.
        
        Returns:
            tuple[dict, int]: (structured_result_dict, latency_ms)
        """
        start_time = time.perf_counter()
        
        fallback_result = {
            "nivel_asignado": "bajo",
            "diagnostico_causa_raiz": "Error de procesamiento técnico",
            "porcentaje_confianza": "0%",
            "respuesta_cliente": "Lo siento, he tenido un problema al procesar tu solicitud. ¿Me lo puedes repetir de nuevo?"
        }

        if not text:
            fallback_result["respuesta_cliente"] = "No te he podido escuchar claramente. ¿Podrías repetir, por favor?"
            return fallback_result, 0

        # Construct dynamic prompt inserting the ESTADO_RED setting
        system_instruction = (
            "Eres el núcleo de Inteligencia Artificial del Agente de Voz de la empresa de telecomunicaciones Miranet SAC (Año 2026). "
            "Tu función es procesar reportes de fallas de internet y actuar de manera síncrona como Operadora Automática y Técnico de Monitoreo.\n\n"
            f"(La variable ESTADO_RED actual es: '{settings.ESTADO_RED}')\n\n"
            "Debes seguir estas REGLAS DE COMPORTAMIENTO al pie de la letra:\n\n"
            "### 1. EVALUACIÓN Y CLASIFICACIÓN (HU-03) \n"
            "Analiza el texto transcrito del cliente y clasifícalo estrictamente en uno de estos 4 niveles:\n"
            "- BAJO: Consultas generales o dudas comerciales.\n"
            "- MEDIO: Falla intermitente, lentitud o caídas esporádicas.\n"
            "- ALTO: Pérdida total del servicio (individual).\n"
            "- CRÍTICO: El cliente menciona palabras como \"masivo\", \"toda la zona\", \"mis vecinos tampoco tienen\" OR la variable ESTADO_RED es igual a 'FALLA_MASIVA'.\n\n"
            "### 2. CONTROL DE AMBIGÜEDAD (HU-04) \n"
            "Si la descripción del cliente es vaga (ej. \"No da\"), tienes prohibido asumir datos. \n"
            "- Formula una pregunta de aclaración específica (Ej: \"¿El problema es en todos sus dispositivos o solo en uno?\").\n"
            "- Máximo puedes hacer 2 preguntas de aclaración antes de derivar el caso.\n\n"
            "### 3. DIAGNÓSTICO DE CAUSA RAÍZ (HU-08) \n"
            "Cruza el reporte con los parámetros simulados de red (ESTADO_RED). Genera una causa raíz técnica probable y asígnale un porcentaje de confianza estimado (ej. \"Saturación de enlace en Nodo - Confianza: 90%\").\n\n"
            "### 4. CONCISIÓN ABSOLUTA EN CANAL DE VOZ (Regla de Oro)\n"
            "Estás hablando por teléfono, NO estás escribiendo un correo. Tus respuestas verbales al cliente deben ser directas, amables y cortas (MÁXIMO 2 ORACIONES o 25 PALABRAS). Está terminantemente prohibido explayarse en explicaciones técnicas innecesarias con el usuario.\n\n"
            "### 5. FORMATO DE SALIDA (Para el Orquestador Backend)\n"
            "Siempre debes estructurar tu respuesta interna devolviendo este formato JSON plano para que el sistema guarde en Supabase (HU-12):\n"
            "{\n"
            '  "nivel_asignado": "[bajo/medio/alto/critico]",\n'
            '  "diagnostico_causa_raiz": "[Diagnóstico técnico breve]",\n'
            '  "porcentaje_confianza": "[0-100%]",\n'
            '  "respuesta_cliente": "[Mensaje hablado súper corto y conciso que escuchará el cliente]"\n'
            "}\n"
            "No incluyas nada fuera del objeto JSON."
        )

        messages = [{"role": "system", "content": system_instruction}]

        if history:
            # Format and filter history to only include last 6 messages
            formatted_history = []
            for msg in history[-6:]:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                # If content is a dict (json string from previous assistant step), parse or extract client response
                if role == "assistant" and content.startswith("{"):
                    try:
                        parsed = json.loads(content)
                        content = parsed.get("respuesta_cliente", content)
                    except Exception:
                        pass
                formatted_history.append({"role": role, "content": content})
            messages.extend(formatted_history)

        messages.append({"role": "user", "content": text})

        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "format": "json",  # Instruct Ollama to output valid JSON
            "options": {
                "temperature": 0.3,
                "num_predict": 192  # Enough space for structured JSON
            }
        }

        try:
            logger.info("Generating structured response from Ollama...")
            response = await self.client.post(
                f"{self.base_url}/api/chat",
                json=payload
            )
            response.raise_for_status()
            
            response_data = response.json()
            response_text = response_data.get("message", {}).get("content", "").strip()
            
            # Parse response
            structured_data = json.loads(response_text)
            
            # Clean and ensure default keys are present
            result = {
                "nivel_asignado": structured_data.get("nivel_asignado", "bajo").lower(),
                "diagnostico_causa_raiz": structured_data.get("diagnostico_causa_raiz", "Diagnóstico genérico"),
                "porcentaje_confianza": structured_data.get("porcentaje_confianza", "50%"),
                "respuesta_cliente": structured_data.get("respuesta_cliente", "Entendido. ¿Me das más detalles?")
            }
            
            latency_ms = int((time.perf_counter() - start_time) * 1000)
            logger.info(f"Structured response generated in {latency_ms}ms: {result}")
            return result, latency_ms

        except (httpx.HTTPError, json.JSONDecodeError, KeyError) as e:
            latency_ms = int((time.perf_counter() - start_time) * 1000)
            logger.error(f"Error during structured response generation: {e}")
            return fallback_result, latency_ms
