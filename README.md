# Miranet VoiceAgent — Sistema de Voz Interactivo en Tiempo Real (2026)

**Miranet VoiceAgent** es una plataforma avanzada de soporte de voz e inteligencia artificial en tiempo real, diseñada específicamente para el procesamiento automático y síncrono de reportes de fallas de internet en la empresa de telecomunicaciones **Miranet SAC** para el año 2026. 

El sistema actúa simultáneamente como **Operadora Automática** (canal de voz directo con el cliente) y **Técnico de Monitoreo** (clasificando incidencias, estimando la causa raíz del problema con su respectiva confianza, y analizando métricas de red en tiempo real).

---

## 🚀 Características Principales

1. **Procesamiento de Voz Asíncrono de Baja Latencia:** Captura y re-muestrea audio del micrófono del cliente a mono PCM de 16-bit a 16kHz, transmitiéndolo a través de WebSockets de manera continua.
2. **Transcripción Local Rápida:** Utiliza una versión optimizada local de **OpenAI Whisper (modelo `tiny`)** ejecutada localmente en la CPU/GPU para transcribir la voz del cliente en tiempo récord.
3. **Núcleo de Inteligencia Artificial (Mistral 7B):** Integrado de forma local mediante **Ollama**, aplicando reglas de negocio y restricciones estrictas a través de un único prompt optimizado:
   - **Evaluación y Clasificación:** Nivel asignado de gravedad (`bajo`, `medio`, `alto`, `critico`).
   - **Control de Ambigüedad:** Detección de reportes vagos para realizar preguntas de aclaración.
   - **Diagnóstico Técnico de Causa Raíz:** Cruza la queja del cliente con el estado actual simulado de la red (`ESTADO_RED`).
   - **Concisión Absoluta:** Respuestas de voz súper cortas y directas (máximo 2 oraciones o 25 palabras).
4. **Persistencia Dual (MySQL & SQLite):** Conexión asíncrona robusta a **MySQL** (`aiomysql`) con detección y creación automática de bases de datos y tablas. Si la instancia de MySQL no está disponible, el sistema cambia dinámicamente y sin interrupciones a una base de datos local **SQLite**.
5. **Interfaz Premium Glassmorphism:** Consola de monitoreo moderna con efectos visuales dinámicos, un osciloscopio interactivo conectado a la API de Web Audio para renderizar las ondas de voz, widgets de latencia/jitter/ancho de banda y síntesis de voz automática (`SpeechSynthesis` de HTML5) para reproducir la respuesta del agente.

---

## 🛠️ Tecnologías y Herramientas Utilizadas

El ecosistema de desarrollo del proyecto está compuesto por las siguientes tecnologías:

* **Lenguaje:** [Python 3.10+](https://www.python.org/) para todo el ecosistema del backend.
* **Framework Web & APIs:** [FastAPI](https://fastapi.tiangolo.com/) y [Uvicorn](https://www.uvicorn.org/) para servir el backend y administrar WebSockets binarios bidireccionales de alta frecuencia.
* **Modelos de Inteligencia Artificial:**
  - **OpenAI Whisper (tiny):** Procesador local de reconocimiento de voz (STT).
  - **Ollama (Mistral 7B):** Motor conversacional local y clasificador de texto configurado con salida estricta en formato JSON.
* **Base de Datos:**
  - **MySQL (Principal):** Mediante el conector asíncrono `aiomysql`.
  - **SQLite (Fallback):** Para portabilidad local sin configuración externa.
* **Frontend:**
  - **Estructura y Lógica:** HTML5 semántico y Vanilla JavaScript.
  - **Estilos:** Vanilla CSS moderno basado en HSL, layouts Grid/Flexbox, efectos translúcidos (Glassmorphism), sombras con degradados neón y variables dinámicas.
  - **Audio y Visualización:** Web Audio API (analizador FFT) y renderizado de ondas mediante Canvas 2D.
  - **Voz del Agente (TTS):** API nativa de `SpeechSynthesis` de HTML5 configurada para idioma español.

---

## 📂 Estructura del Proyecto

El proyecto está organizado en una estructura limpia y desacoplada:

```text
miranet-voiceagent/
│
├── backend/                        # Lógica del servidor y Agentes de IA
│   ├── agents/                     # Módulos de toma de decisiones
│   │   ├── __init__.py             # Inicializador del paquete de agentes
│   │   ├── transcriber.py          # Transcriptor local de audio (Whisper)
│   │   ├── responder.py            # Generador de respuestas y clasificación (Ollama LLM)
│   │   ├── network_monitor.py      # Calculadora en tiempo real de jitter, pérdida y ancho de banda
│   │   ├── classifier.py           # Agente clasificador (mantenido para retrocompatibilidad)
│   │   └── orchestrator.py         # Orquestador del flujo y persistencia de datos
│   │
│   ├── db/                         # Configuración y consultas de base de datos
│   │   └── database.py             # Administrador de MySQL (aiomysql) y SQLite
│   │
│   ├── config.py                   # Lector de configuraciones del sistema (.env)
│   └── main.py                     # Punto de entrada de FastAPI y servidor de WebSockets
│
├── frontend/                       # Interfaz gráfica del usuario
│   ├── index.html                  # Estructura del panel de monitoreo y consola de voz
│   ├── index.css                   # Diseño visual premium, colores y animaciones
│   └── index.js                    # Captura de micrófono, WebSocket y síntesis de voz (TTS)
│
├── models/                         # Caché local de modelos descargados (Whisper)
│   └── whisper/                    # Pesos descargados localmente
│
├── .env                            # Archivo de variables de entorno del sistema
├── requirements.txt                # Dependencias de Python requeridas
├── db_setup.sql                    # Script SQL para base de datos con datos de prueba
├── test_client.py                  # Cliente de terminal para simulación de voz
└── README.md                       # Documentación principal del sistema
```

---

## ⚙️ Configuración e Instalación

Sigue estos pasos para instalar e iniciar el proyecto en tu entorno local:

### Requisitos Previos
1. Tener instalado [Python 3.10+](https://www.python.org/downloads/).
2. Tener instalado y corriendo [Ollama](https://ollama.com/).
3. Tener una base de datos [MySQL](https://www.mysql.com/) activa (opcional, el sistema creará todo automáticamente o usará SQLite como fallback si no está corriendo).

### Paso 1: Clonar e Instalar Dependencias
Abre tu consola de comandos en la carpeta del proyecto y ejecuta:

```bash
# Instalar los paquetes requeridos de Python
pip install -r requirements.txt
```

### Paso 2: Descargar el Modelo en Ollama
Asegúrate de que Ollama está activo en segundo plano y descarga el modelo Mistral:

```bash
ollama pull mistral
```

### Paso 3: Configurar Variables de Entorno
Crea o edita el archivo `.env` en la raíz del proyecto para adecuar los accesos a tu base de datos local y simular el estado de la red:

```ini
# Configuración de Base de Datos MySQL
DB_HOST=127.0.0.1
DB_PORT=3306
DB_USER=***
DB_PASSWORD=***
DB_NAME=miranet_voiceagent

# Configuración de Ollama
OLLAMA_BASE_URL=http://127.0.0.1:8000
OLLAMA_MODEL=mistral

# Configuración de Whisper
WHISPER_MODEL_NAME=tiny
WHISPER_DOWNLOAD_ROOT=D:\miranet-voiceagent\models\whisper

# Parámetro de Simulación de Red (ESTABLE o FALLA_MASIVA)
ESTADO_RED=ESTABLE
```

---

## 🏁 Inicio de Trabajo y Ejecución

Una vez completada la configuración, puedes arrancar el agente con los siguientes comandos:

### 1. Iniciar el Servidor Backend
Ejecuta el script principal de inicialización en la consola:

```bash
python backend/main.py
```
*El backend iniciará las conexiones con la base de datos, descargará o cargará el modelo local de Whisper en memoria, y encenderá el servidor ASGI en el puerto `8000`.*

### 2. Acceso a la Interfaz Gráfica
Abre tu navegador de preferencia e ingresa al siguiente enlace:

👉 **[http://localhost:8000/](http://localhost:8000/)**

> [!TIP]
> **Compatibilidad con Live Server:** Si estás utilizando la extensión *Live Server* de Visual Studio Code (ejecutando la web en el puerto `5500`), el cliente frontend redirigirá de manera automática todos los servicios de API y canales WebSockets al puerto del backend (`8000`), por lo que puedes interactuar y depurar estilos directamente desde ahí.

### 3. Realizar una Simulación por Consola (Opcional)
Si deseas verificar las conexiones y la respuesta de red sin usar el micrófono, puedes correr el cliente de prueba sintético:

```bash
python test_client.py
```
*Este cliente transmitirá un tono de audio simulado a través del canal WebSockets, indicando en consola las latencias de procesamiento y reportes de jitter en tiempo real.*
