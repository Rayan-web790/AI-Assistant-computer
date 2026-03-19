import os
import io
import time
import random
import threading
import asyncio
import sounddevice as sd
import numpy as np
from PIL import Image, ImageTk
import tkinter as tk
from tkinter.scrolledtext import ScrolledText
import re
from elevenlabs import VoiceSettings
from elevenlabs.client import ElevenLabs
from dotenv import load_dotenv

load_dotenv()

def normalize_punctuation(text: str) -> str:
    text = re.sub(r'\.\s+', ', ', text)
    text = re.sub(r'!\s+', ', ', text)
    text = re.sub(r'\?\s+', ', ', text)
    if text.endswith("."):
        text = text[:-1]
    return text.strip()

class VoiceImagePlayer:
    def __init__(self, face_path, size=(760, 760)):
        self.root = tk.Tk()
        self.root.title("R.Y.A.N")
        self.root.resizable(False, False)
        self.root.geometry("760x900")

        self.fixed_size = size
        self.face_original = Image.open(face_path).resize(self.fixed_size, Image.LANCZOS)
        self.face_label = tk.Label(self.root, bg="#001f4d", borderwidth=0, highlightthickness=0)
        self.face_label.place(relx=0.5, rely=0.4, anchor="center")

        self.scale = 1.0
        self.playing = False

        self.text_box = ScrolledText(
            self.root,
            fg="#00ffff",
            bg="#001f4d",
            insertbackground="#00ffff",
            height=12,
            borderwidth=0,
            highlightthickness=0,
            relief="flat",
            wrap="word",
            font=("Consolas", 10),
            padx=10,
            pady=10
        )
        self.text_box.place(relx=0.5, rely=0.85, anchor="center")

        self.animate()
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        
    def on_close(self):
        os._exit(0)

    def write_log(self, text):
        self.text_box.configure(state="normal")
        self.text_box.insert(tk.END, text + "\n")
        self.text_box.see(tk.END)
        self.text_box.configure(state="disabled")

    def start_animation(self):
        self.root.after(0, lambda: setattr(self, 'playing', True))

    def stop_animation(self):
        self.root.after(0, lambda: setattr(self, 'playing', False))

    def animate(self):
        if self.playing:
            self.scale += random.uniform(-0.015, 0.02)
            self.scale = min(max(self.scale, 1.02), 1.10)
        else:
            if abs(self.scale - 1.0) < 0.003:
                self.scale = 1.0
            elif self.scale > 1.0:
                self.scale -= 0.009
            else:
                self.scale += 0.005

        new_size = (int(self.fixed_size[0] * self.scale), int(self.fixed_size[1] * self.scale))
        resized = self.face_original.resize(new_size, Image.LANCZOS)
        tk_img = ImageTk.PhotoImage(resized)
        self.face_label.configure(image=tk_img)
        self.face_label.image = tk_img
        self.root.after(50, self.animate)

class ElevenLabsSpeaker:
    def __init__(self, player: VoiceImagePlayer):
        self.api_key = os.getenv("ELEVENLABS_API_KEY")
        self.voice_id = os.getenv("ELEVENLABS_VOICE_ID", "pNInz6obpgDQGcFmaJgB")
        self.client = ElevenLabs(api_key=self.api_key)
        self.player = player

    def stream_speech(self, text_gen, start_time):
        """
        Streams generated text to ElevenLabs and plays immediately using Raw PCM.
        Uses convert_realtime to support text input streaming from a generator.
        """
        def _stream_thread():
            try:
                first_byte_time = None
                playback_started = False
                
                # Use mp3_44100_128 which is available on all tiers (including Free)
                audio_stream = self.client.text_to_speech.convert_realtime(
                    text=text_gen,
                    voice_id=self.voice_id,
                    model_id="eleven_turbo_v2",
                    output_format="mp3_44100_128",
                    voice_settings=VoiceSettings(
                        stability=0.3,
                        similarity_boost=0.7,
                        style=0.0,
                        use_speaker_boost=True
                    )
                )

                # For MP3 streaming without MPV or FFMPEG, we use miniaudio (zero-dependency).
                import io
                import miniaudio

                def _play_mp3_stream():
                    nonlocal first_byte_time, playback_started
                    full_mp3_data = bytearray()
                    
                    for chunk in audio_stream:
                        if first_byte_time is None:
                            first_byte_time = time.time()
                            print(f"[TTS FIRST BYTE] {first_byte_time - start_time:.3f}s")
                        
                        full_mp3_data.extend(chunk)
                        
                        # Once we have enough data to start (e.g., 8KB), try to play
                        if not playback_started and len(full_mp3_data) > 8000:
                            playback_started = True
                            print(f"[PLAYBACK START] {time.time() - start_time:.3f}s")
                            self.player.start_animation()
                    
                    if len(full_mp3_data) > 0:
                        try:
                            # Convert bytearray to bytes for miniaudio compatibility
                            mp3_bytes = bytes(full_mp3_data)
                            # Decode MP3 bytes directly to PCM using miniaudio
                            decoded = miniaudio.decode(mp3_bytes)
                            
                            # Play the raw samples via sounddevice
                            samples = np.frombuffer(decoded.samples, dtype=np.int16)
                            # miniaudio decode returns mono/stereo correctly
                            if decoded.nchannels == 2:
                                samples = samples.reshape((-1, 2))
                            
                            sd.play(samples, samplerate=decoded.sample_rate)
                            sd.wait()
                        except Exception as decode_err:
                            print(f"❌ Audio Decode Error: {decode_err}")
                    
                    self.player.stop_animation()

                _play_mp3_stream()

            except Exception as e:
                print(f"❌ ElevenLabs Error: {e}")
                self.player.stop_animation()

        threading.Thread(target=_stream_thread, daemon=True).start()
