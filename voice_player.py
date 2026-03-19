import os
import io
import time
import random
import threading
import asyncio
import sounddevice as sd
import numpy as np
from PIL import Image, ImageTk, ImageDraw
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
    return text.strip()

class VoiceImagePlayer:
    def __init__(self, face_path, size=(300, 300)): # Smaller size for centered orb
        self.root = tk.Tk()
        self.root.title("J.A.R.V.I.S")
        self.root.resizable(False, False)
        
        # Load background to get dimensions
        bg_path = "ui_background.png"
        if not os.path.exists(bg_path):
            bg_path = face_path # Fallback

        self.bg_image_pil = Image.open(bg_path)
        # Resize background to a reasonable desktop window size if too big
        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        target_w = 1000
        target_h = int(target_w * (self.bg_image_pil.height / self.bg_image_pil.width))
        if target_h > 800:
            target_h = 800
            target_w = int(target_h * (self.bg_image_pil.width / self.bg_image_pil.height))
            
        self.bg_image_pil = self.bg_image_pil.resize((target_w, target_h), Image.LANCZOS)
        self.root.geometry(f"{target_w}x{target_h}")
        self.target_w = target_w # Store for later use in bubble positioning
        self.target_h = target_h # Store for later use in bubble positioning

        self.canvas = tk.Canvas(self.root, width=target_w, height=target_h, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)

        self.bg_image_tk = ImageTk.PhotoImage(self.bg_image_pil)
        self.canvas.create_image(0, 0, image=self.bg_image_tk, anchor="nw")

        self.fixed_size = size
        self.face_original = Image.open(face_path).resize(self.fixed_size, Image.LANCZOS)
        self.face_tk = ImageTk.PhotoImage(self.face_original)
        self.face_item = self.canvas.create_image(target_w//2, target_h//2, image=self.face_tk, anchor="center")

        self.user_bubble = None
        self.ai_bubble = None
        self.user_text_item = None
        self.ai_text_item = None
        self.user_bubble_img = None
        self.ai_bubble_img = None
        self.face_tk_current = self.face_tk # Initial reference

        self.scale = 1.0
        self.playing = False
        self.animate()
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def on_close(self):
        os._exit(0)

    def create_bubble_image(self, width, height, color=(0, 255, 255, 40)): # 40 is alpha
        # Create a semi-transparent rounded rectangle image
        img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        radius = 15
        draw.rounded_rectangle([0, 0, width, height], radius=radius, fill=color, outline=(color[0], color[1], color[2], 150), width=2)
        return ImageTk.PhotoImage(img)

    def show_user_message(self, text):
        if self.user_bubble is not None: self.canvas.delete(self.user_bubble)
        if self.user_text_item is not None: self.canvas.delete(self.user_text_item)
        
        # Wrap text
        max_width = 300
        words = text.split()
        lines = []
        current_line = ""
        for word in words:
            if len(current_line + word) < 30: # Rough estimate
                current_line += word + " "
            else:
                lines.append(current_line)
                current_line = word + " "
        lines.append(current_line)
        wrapped_text = "\n".join(lines).strip()

        h = len(lines) * 25 + 20
        self.user_bubble_img = self.create_bubble_image(max_width, h, color=(0, 150, 255, 60))
        self.user_bubble = self.canvas.create_image(50, 100, image=self.user_bubble_img, anchor="nw")
        self.user_text_item = self.canvas.create_text(65, 115, text=wrapped_text, fill="white", font=("Inter", 12), anchor="nw", width=270)

    def show_ai_message(self, text):
        if self.ai_bubble is not None: self.canvas.delete(self.ai_bubble)
        if self.ai_text_item is not None: self.canvas.delete(self.ai_text_item)

        # Wrap text
        max_width = 350
        words = text.split()
        lines = []
        current_line = ""
        for word in words:
            if len(current_line + word) < 40:
                current_line += word + " "
            else:
                lines.append(current_line)
                current_line = word + " "
        lines.append(current_line)
        wrapped_text = "\n".join(lines).strip()

        h = len(lines) * 25 + 20
        self.ai_bubble_img = self.create_bubble_image(max_width, h, color=(200, 200, 255, 40))
        # Position at bottom right
        self.ai_bubble = self.canvas.create_image(self.target_w - max_width - 50, self.target_h - h - 150, image=self.ai_bubble_img, anchor="nw")
        self.ai_text_item = self.canvas.create_text(self.target_w - max_width - 35, self.target_h - h - 135, text=wrapped_text, fill="white", font=("Inter", 12), anchor="nw", width=320)

    def write_log(self, text):
        # Compatibility with main.py, routes to bubbles if possible
        if text.startswith("You:"):
            self.show_user_message(text[4:].strip())
        elif text.startswith("AI:"):
            self.show_ai_message(text[3:].strip())
        print(text)

    def start_animation(self):
        self.root.after(0, lambda: setattr(self, 'playing', True))

    def stop_animation(self):
        self.root.after(0, lambda: setattr(self, 'playing', False))

    def animate(self):
        if self.playing:
            self.scale += random.uniform(-0.015, 0.02)
            self.scale = min(max(self.scale, 1.02), 1.15)
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
        self.canvas.itemconfig(self.face_item, image=tk_img)
        self.face_tk_current = tk_img # Keep reference on self
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
                
                def _text_accumulator(gen):
                    full_text = ""
                    for token in gen:
                        full_text += token
                        yield token
                    self.player.write_log(f"AI: {full_text}")

                # Use mp3_44100_128 which is available on all tiers (including Free)
                audio_stream = self.client.text_to_speech.convert_realtime(
                    text=_text_accumulator(text_gen),
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
