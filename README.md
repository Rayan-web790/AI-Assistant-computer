# AI Jarvis Assistant for Computer

A high-performance, voice-activated AI assistant for desktop interaction and automation. This project leverages Groq’s low-latency LLM inference to provide real-time, "Jarvis-like" responses, featuring a modular architecture for specialized commands and high-quality voice output.

## Features

- **Voice Interaction**: Advanced speech-to-text and text-to-speech integration.
- **High-Performance AI**: Powered by Groq's LLM models (e.g., Llama 3) for near-instant reasoning.
- **Jarvis Interaction Style**: Professional and helpful responses (always including "sir").
- **Visual Interface**: Dynamic "AI face" display using Tkinter.
- **Modular Hardware/Aircraft Logic**: Specialized modules for handling complex domain-specific tasks.
- **ElevenLabs Integration**: Natural-sounding voice synthesis.

## Prerequisites

- Python 3.8+
- [Groq API Key](https://console.groq.com/keys)
- [ElevenLabs API Key](https://elevenlabs.io/api) (Optional, depending on your configuration)

## Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/your-username/AI-Assistant-computer.git
   cd AI-Assistant-computer
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**:
   Create a `.env` file in the root directory based on the `.env.example` provided:
   ```bash
   cp .env.example .env
   ```
   *Edit the `.env` file and add your actual API keys.*

## Usage

1. **Start the assistant**:
   Run `main.py` to begin the voice-activated loop:
   ```bash
   python main.py
   ```
   *You can also use the `start.bat` on Windows for a quick launch.*

2. **Interacting**:
   Speak your commands after the prompt. The assistant will respond with text and voice.

## Customization

- **Voice**: Change the voice settings in `voice_player.py`.
- **Logic**: Modify the AI's behavior in `groq_ai.py`.
- **UI**: Replace `face.png` with your own design.

## Author

- **Rayan-web790**

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
