import asyncio
import threading
import time
from voice_player import VoiceImagePlayer, ElevenLabsSpeaker
from speech_to_text import record_voice
from groq_ai import get_response_stream
from aircraft_module import handle_aircraft_command

async def get_voice_input():
    return await asyncio.to_thread(record_voice)

def text_chunker(token_generator):
    """
    Yields chunks of text based on sentence boundaries or word count.
    """
    buffer = ""
    word_count = 0
    
    for token in token_generator:
        buffer += token
        # Count words in this token
        words_in_token = len(token.strip().split())
        word_count += words_in_token
        
        # Check for sentence boundaries or word limit
        if any(punct in token for punct in [".", "!", "?"]) or word_count >= 10:
            if buffer.strip():
                yield buffer
                buffer = ""
                word_count = 0
    
    # Flush remaining buffer
    if buffer.strip():
        yield buffer

async def ai_loop(player):
    speaker = ElevenLabsSpeaker(player)

    while True:
        user_text = await get_voice_input()
        if not user_text:
            continue

        handled = handle_aircraft_command(user_text, player)
        if handled:
            continue

        # --- Request Start ---
        start_time = time.time()
        print(f"\n[START] 0.000s")
        print(f"👤 You: {user_text}")
        player.write_log(f"You: {user_text}")

        # 1. Start LLM streaming (Generator)
        token_gen = get_response_stream(user_text, start_time)
        
        # 2. Text Chunker (Sentence ends or 10 words)
        chunk_gen = text_chunker(token_gen)
        
        # 3. Start TTS streaming (Parallel Thread)
        speaker.stream_speech(chunk_gen, start_time)

def main_loop():
    player = VoiceImagePlayer("face.png", size=(900, 900))

    def thread_target():
        asyncio.run(ai_loop(player))

    threading.Thread(target=thread_target, daemon=True).start()
    player.root.mainloop()

if __name__ == "__main__":
    main_loop()
