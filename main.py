
import os
import sys
import time
import shutil
import threading
import subprocess
import queue
from pathlib import Path
from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox

import numpy as np
import mss
import imageio_ffmpeg
import soundcard as sc
import soundfile as sf


BG = "#15191d"
PANEL = "#20272d"
PANEL2 = "#29333a"
ACCENT = "#35d6c2"
WHITE = "#f1f5f6"
MUTED = "#93a1a8"
RED = "#ff555d"

WIDTH = 1280
HEIGHT = 720
SAMPLE_RATE = 48000


def output_folder():
    folder = Path.home() / "Videos" / "LaPauta Capture"
    folder.mkdir(parents=True, exist_ok=True)
    return folder


def audio_worker(device, path, channels, stop_event, errors):
    try:
        with sf.SoundFile(
            str(path),
            mode="w",
            samplerate=SAMPLE_RATE,
            channels=channels,
            subtype="PCM_16"
        ) as wav:

            with device.recorder(
                samplerate=SAMPLE_RATE,
                channels=channels
            ) as recorder:

                while not stop_event.is_set():
                    data = recorder.record(numframes=1024)

                    if data.ndim == 1:
                        data = data.reshape(-1, 1)

                    if data.shape[1] == 1 and channels == 2:
                        data = np.repeat(data, 2, axis=1)

                    if data.shape[1] > channels:
                        data = data[:, :channels]

                    if data.shape[1] < channels:
                        data = np.repeat(data, channels, axis=1)

                    wav.write(np.clip(data, -1, 1))

    except Exception as exc:
        errors.append(str(exc))


class LaPautaCapture:

    def __init__(self, root):
        self.root = root
        self.root.title("LaPauta Capture Studio")
        self.root.geometry("850x610")
        self.root.minsize(760, 560)
        self.root.configure(bg=BG)

        self.recording = False
        self.stop_event = threading.Event()
        self.worker = None
        self.start_time = 0
        self.errors = []

        self.fps = tk.IntVar(value=8)
        self.resolution = tk.StringVar(value="720p")
        self.capture_mic = tk.BooleanVar(value=True)
        self.capture_system = tk.BooleanVar(value=True)

        self.build_interface()
        self.root.protocol("WM_DELETE_WINDOW", self.close_app)

    def build_interface(self):

        header = tk.Frame(self.root, bg=BG)
        header.pack(fill="x", padx=28, pady=(23, 10))

        tk.Label(
            header,
            text="LA PAUTA",
            bg=BG,
            fg=ACCENT,
            font=("Arial", 12, "bold")
        ).pack(anchor="w")

        tk.Label(
            header,
            text="CAPTURE STUDIO",
            bg=BG,
            fg=WHITE,
            font=("Arial", 25, "bold")
        ).pack(anchor="w")

        tk.Label(
            header,
            text="SCREEN RECORDING SYSTEM  /  WINDOWS 64-BIT",
            bg=BG,
            fg=MUTED,
            font=("Arial", 9)
        ).pack(anchor="w", pady=(3, 0))

        separator = tk.Frame(self.root, bg=ACCENT, height=2)
        separator.pack(fill="x", padx=28, pady=12)

        main = tk.Frame(self.root, bg=PANEL)
        main.pack(fill="both", expand=True, padx=28, pady=10)

        self.status = tk.Label(
            main,
            text="● SISTEMA LISTO",
            bg=PANEL,
            fg=ACCENT,
            font=("Arial", 12, "bold")
        )
        self.status.pack(anchor="w", padx=22, pady=(20, 12))

        self.timer = tk.Label(
            main,
            text="00:00:00",
            bg=PANEL,
            fg=WHITE,
            font=("Consolas", 35, "bold")
        )
        self.timer.pack(pady=15)

        options = tk.Frame(main, bg=PANEL)
        options.pack(fill="x", padx=22, pady=12)

        self.add_option(
            options, "FPS", self.fps,
            ["8", "15", "30"]
        )

        self.add_option(
            options, "RESOLUCIÓN", self.resolution,
            ["720p", "1080p"]
        )

        audio = tk.Frame(main, bg=PANEL2)
        audio.pack(fill="x", padx=22, pady=15)

        tk.Label(
            audio,
            text="CAPTURA DE AUDIO",
            bg=PANEL2,
            fg=ACCENT,
            font=("Arial", 10, "bold")
        ).pack(anchor="w", padx=15, pady=(12, 5))

        tk.Checkbutton(
            audio,
            text="Micrófono",
            variable=self.capture_mic,
            bg=PANEL2,
            fg=WHITE,
            selectcolor=BG,
            activebackground=PANEL2,
            activeforeground=ACCENT,
            font=("Arial", 10)
        ).pack(anchor="w", padx=15)

        tk.Checkbutton(
            audio,
            text="Audio del sistema / DAW",
            variable=self.capture_system,
            bg=PANEL2,
            fg=WHITE,
            selectcolor=BG,
            activebackground=PANEL2,
            activeforeground=ACCENT,
            font=("Arial", 10)
        ).pack(anchor="w", padx=15, pady=(0, 12))

        buttons = tk.Frame(main, bg=PANEL)
        buttons.pack(pady=22)

        self.start_button = tk.Button(
            buttons,
            text="●  INICIAR GRABACIÓN",
            command=self.start_recording,
            bg=ACCENT,
            fg="#101719",
            activebackground="#70eadc",
            font=("Arial", 12, "bold"),
            relief="flat",
            padx=25,
            pady=14,
            cursor="hand2"
        )
        self.start_button.pack(side="left", padx=8)

        self.stop_button = tk.Button(
            buttons,
            text="■  DETENER",
            command=self.stop_recording,
            bg="#414a50",
            fg=WHITE,
            activebackground="#56636b",
            font=("Arial", 12, "bold"),
            relief="flat",
            padx=25,
            pady=14,
            cursor="hand2",
            state="disabled"
        )
        self.stop_button.pack(side="left", padx=8)

        footer = tk.Label(
            self.root,
            text="LA PAUTA AUDIO  •  LOW RESOURCE RECORDING",
            bg=BG,
            fg=MUTED,
            font=("Arial", 9)
        )
        footer.pack(pady=12)

    def add_option(self, parent, label, variable, values):
        box = tk.Frame(parent, bg=PANEL)
        box.pack(side="left", expand=True, fill="x", padx=5)

        tk.Label(
            box,
            text=label,
            bg=PANEL,
            fg=MUTED,
            font=("Arial", 9, "bold")
        ).pack(anchor="w")

        combo = ttk.Combobox(
            box,
            textvariable=variable,
            values=values,
            state="readonly",
            width=12
        )
        combo.pack(anchor="w", pady=7)

    def start_recording(self):

        if self.recording:
            return

        self.recording = True
        self.stop_event.clear()
        self.errors = []

        self.start_button.config(state="disabled")
        self.stop_button.config(state="normal")

        self.status.config(
            text="● GRABANDO",
            fg=RED
        )

        self.start_time = time.time()
        self.update_timer()

        self.worker = threading.Thread(
            target=self.record_worker,
            daemon=True
        )
        self.worker.start()

    def stop_recording(self):

        if not self.recording:
            return

        self.status.config(
            text="● FINALIZANDO ARCHIVO...",
            fg=ACCENT
        )

        self.stop_button.config(state="disabled")
        self.stop_event.set()

    def update_timer(self):

        if self.recording:
            elapsed = int(time.time() - self.start_time)

            hours = elapsed // 3600
            minutes = (elapsed % 3600) // 60
            seconds = elapsed % 60

            self.timer.config(
                text=f"{hours:02}:{minutes:02}:{seconds:02}"
            )

            self.root.after(500, self.update_timer)

    def record_worker(self):

        folder = output_folder()

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        final_file = folder / f"LaPauta_{timestamp}.mp4"
        video_file = folder / f"video_{timestamp}.mp4"

        system_wav = folder / f"system_{timestamp}.wav"
        mic_wav = folder / f"mic_{timestamp}.wav"

        audio_threads = []

        try:
            width, height = (
                (1280, 720)
                if self.resolution.get() == "720p"
                else (1920, 1080)
            )

            fps = int(self.fps.get())

            if self.capture_system.get():
                try:
                    speaker = sc.default_speaker()

                    loopback = sc.get_microphone(
                        speaker.name,
                        include_loopback=True
                    )

                    thread = threading.Thread(
                        target=audio_worker,
                        args=(
                            loopback,
                            system_wav,
                            2,
                            self.stop_event,
                            self.errors
                        ),
                        daemon=True
                    )

                    thread.start()
                    audio_threads.append(thread)

                except Exception as exc:
                    self.errors.append(
                        "Audio del sistema: " + str(exc)
                    )

            if self.capture_mic.get():
                try:
                    microphone = sc.default_microphone()

                    thread = threading.Thread(
                        target=audio_worker,
                        args=(
                            microphone,
                            mic_wav,
                            1,
                            self.stop_event,
                            self.errors
                        ),
                        daemon=True
                    )

                    thread.start()
                    audio_threads.append(thread)

                except Exception as exc:
                    self.errors.append(
                        "Micrófono: " + str(exc)
                    )

            ffmpeg_writer = imageio_ffmpeg.write_frames(
                str(video_file),
                (width, height),
                fps=fps,
                codec="libx264",
                pix_fmt_in="rgb24",
                quality=8,
                macro_block_size=1,
                output_params=[
                    "-preset", "ultrafast",
                    "-crf", "30",
                    "-pix_fmt", "yuv420p"
                ],
                ffmpeg_log_level="error"
            )

            ffmpeg_writer.send(None)

            interval = 1.0 / fps
            next_frame = time.monotonic()

            with mss.mss() as screen:

                monitor = screen.monitors[0]

                while not self.stop_event.is_set():

                    screenshot = np.asarray(
                        screen.grab(monitor)
                    )

                    frame = screenshot[:, :, :3][:, :, ::-1]

                    import cv2

                    frame = cv2.resize(
                        frame,
                        (width, height),
                        interpolation=cv2.INTER_AREA
                    )

                    ffmpeg_writer.send(
                        np.ascontiguousarray(frame).tobytes()
                    )

                    next_frame += interval

                    delay = next_frame - time.monotonic()

                    if delay > 0:
                        self.stop_event.wait(delay)
                    else:
                        next_frame = time.monotonic()

            ffmpeg_writer.close()

            for thread in audio_threads:
                thread.join(timeout=10)

            self.finish_recording(
                video_file,
                system_wav,
                mic_wav,
                final_file
            )

        except Exception as exc:

            self.errors.append(str(exc))

            self.stop_event.set()

            self.root.after(
                0,
                self.recording_failed,
                str(exc)
            )

    def finish_recording(
        self,
        video_file,
        system_wav,
        mic_wav,
        final_file
    ):

        try:
            ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()

            audio_files = []

            if system_wav.exists() and system_wav.stat().st_size > 100:
                audio_files.append(system_wav)

            if mic_wav.exists() and mic_wav.stat().st_size > 100:
                audio_files.append(mic_wav)

            if audio_files:

                command = [ffmpeg, "-y", "-i", str(video_file)]

                for audio in audio_files:
                    command.extend(["-i", str(audio)])

                if len(audio_files) == 2:
                    command.extend([
                        "-filter_complex",
                        "[1:a][2:a]amix=inputs=2:duration=longest:normalize=0[a]",
                        "-map", "0:v",
                        "-map", "[a]"
                    ])
                else:
                    command.extend([
                        "-map", "0:v",
                        "-map", "1:a"
                    ])

                command.extend([
                    "-c:v", "copy",
                    "-c:a", "aac",
                    "-b:a", "128k",
                    "-shortest",
                    str(final_file)
                ])

                subprocess.run(
                    command,
                    check=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.PIPE
                )

                video_file.unlink(missing_ok=True)

            else:
                shutil.move(str(video_file), str(final_file))

            system_wav.unlink(missing_ok=True)
            mic_wav.unlink(missing_ok=True)

            self.root.after(
                0,
                self.recording_finished,
                str(final_file)
            )

        except Exception as exc:

            self.errors.append(
                "Finalización de audio/vídeo: " + str(exc)
            )

            if video_file.exists():
                shutil.move(str(video_file), str(final_file))

            self.root.after(
                0,
                self.recording_finished,
                str(final_file)
            )

    def recording_finished(self, path):

        self.recording = False

        self.start_button.config(state="normal")
        self.stop_button.config(state="disabled")

        self.status.config(
            text="● GRABACIÓN TERMINADA",
            fg=ACCENT
        )

        self.timer.config(text="00:00:00")

        if self.errors:
            messagebox.showwarning(
                "LaPauta Capture",
                "El vídeo se guardó, pero hubo problemas "
                "con alguna fuente de audio:\n\n"
                + "\n".join(self.errors)
                + "\n\nArchivo:\n" + path
            )
        else:
            messagebox.showinfo(
                "LaPauta Capture Studio",
                "Grabación guardada correctamente:\n\n"
                + path
            )

    def recording_failed(self, error):

        self.recording = False

        self.start_button.config(state="normal")
        self.stop_button.config(state="disabled")

        self.status.config(
            text="● ERROR DE GRABACIÓN",
            fg=RED
        )

        messagebox.showerror(
            "Error",
            "No se pudo completar la grabación:\n\n" + error
        )

    def close_app(self):

        if self.recording:
            if messagebox.askyesno(
                "LaPauta Capture",
                "¿Deseas detener la grabación y cerrar?"
            ):
                self.stop_recording()
                self.root.after(1000, self.close_app)
            return

        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = LaPautaCapture(root)
    root.mainloop()
        
