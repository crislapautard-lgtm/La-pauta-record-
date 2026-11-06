
import os
import sys
import time
import shutil
import tempfile
import threading
import subprocess
import tkinter as tk
from tkinter import filedialog, messagebox

import numpy as np
import cv2
import mss
import sounddevice as sd
import soundfile as sf


APP_NAME = "La Pauta Capture"
FPS = 6
SCREEN_SCALE = 0.35
AUDIO_RATE = 22050
AUDIO_CHANNELS = 1


def find_ffmpeg():
    possible_paths = []

    if getattr(sys, "frozen", False):
        possible_paths.append(
            os.path.join(sys._MEIPASS, "ffmpeg.exe")
        )
        possible_paths.append(
            os.path.join(os.path.dirname(sys.executable), "ffmpeg.exe")
        )

    possible_paths.append(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "ffmpeg.exe")
    )

    for path in possible_paths:
        if os.path.isfile(path):
            return path

    return shutil.which("ffmpeg")


class LaPautaCapture:

    def __init__(self, root):
        self.root = root
        self.root.title(APP_NAME)
        self.root.geometry("440x270")
        self.root.resizable(False, False)
        self.root.configure(bg="#17191c")

        self.recording = False
        self.stop_event = threading.Event()
        self.capture_thread = None

        self.audio_stream = None
        self.audio_file = None
        self.audio_path = None

        self.output_path = None
        self.video_path = None
        self.temp_dir = None

        self.capture_error = None
        self.audio_error = None

        self.create_interface()

    def create_interface(self):
        title = tk.Label(
            self.root,
            text="LA PAUTA",
            font=("Arial", 23, "bold"),
            fg="#42d6c5",
            bg="#17191c"
        )
        title.pack(pady=(18, 0))

        subtitle = tk.Label(
            self.root,
            text="CAPTURE STUDIO",
            font=("Arial", 10, "bold"),
            fg="#eeeeee",
            bg="#17191c"
        )
        subtitle.pack(pady=(0, 16))

        info = tk.Label(
            self.root,
            text="6 FPS  |  35% PANTALLA  |  COLOR NORMAL\n"
                 "AUDIO: 22050 Hz  |  MONO  |  PCM 8 BITS",
            font=("Arial", 9),
            fg="#aeb8bd",
            bg="#17191c",
            justify="center"
        )
        info.pack(pady=5)

        self.start_button = tk.Button(
            self.root,
            text="INICIAR GRABACIÓN",
            font=("Arial", 11, "bold"),
            bg="#42d6c5",
            fg="#101719",
            activebackground="#63e5d5",
            relief="flat",
            width=25,
            height=2,
            command=self.start_recording
        )
        self.start_button.pack(pady=(15, 8))

        self.stop_button = tk.Button(
            self.root,
            text="DETENER Y GUARDAR",
            font=("Arial", 10, "bold"),
            bg="#30363c",
            fg="#ffffff",
            activebackground="#454d54",
            relief="flat",
            width=25,
            height=2,
            state="disabled",
            command=self.stop_recording
        )
        self.stop_button.pack(pady=5)

        self.status = tk.Label(
            self.root,
            text="Listo para grabar",
            font=("Arial", 9),
            fg="#42d6c5",
            bg="#17191c"
        )
        self.status.pack(pady=12)

    def set_status(self, message):
        self.status.config(text=message)

    def audio_callback(self, indata, frames, timing, status):
        if self.audio_file is not None:
            try:
                self.audio_file.write(indata)
            except Exception as error:
                self.audio_error = str(error)
                self.stop_event.set()

    def start_audio(self):
        self.audio_path = os.path.join(
            self.temp_dir, "audio.wav"
        )

        try:
            self.audio_file = sf.SoundFile(
                self.audio_path,
                mode="w",
                samplerate=AUDIO_RATE,
                channels=AUDIO_CHANNELS,
                subtype="PCM_U8"
            )

            self.audio_stream = sd.InputStream(
                samplerate=AUDIO_RATE,
                channels=AUDIO_CHANNELS,
                dtype="int16",
                callback=self.audio_callback
            )

            self.audio_stream.start()
            return True

        except Exception as error:
            self.audio_error = str(error)

            if self.audio_stream is not None:
                try:
                    self.audio_stream.close()
                except Exception:
                    pass

            self.audio_stream = None

            if self.audio_file is not None:
                try:
                    self.audio_file.close()
                except Exception:
                    pass

            self.audio_file = None
            return False

    def close_audio(self):
        if self.audio_stream is not None:
            try:
                self.audio_stream.stop()
            except Exception:
                pass

            try:
                self.audio_stream.close()
            except Exception:
                pass

            self.audio_stream = None

        if self.audio_file is not None:
            try:
                self.audio_file.close()
            except Exception:
                pass

            self.audio_file = None

    def start_recording(self):
        output = filedialog.asksaveasfilename(
            title="Guardar grabación",
            defaultextension=".mp4",
            filetypes=[("Video MP4", "*.mp4")],
            initialfile="LaPautaCapture.mp4"
        )

        if not output:
            return

        ffmpeg = find_ffmpeg()

        if not ffmpeg:
            messagebox.showerror(
                "FFmpeg no encontrado",
                "No se encontró ffmpeg.exe.\n"
                "Revisa la compilación de GitHub."
            )
            return

        self.output_path = output
        self.temp_dir = tempfile.mkdtemp(
            prefix="LaPautaCapture_"
        )

        self.video_path = os.path.join(
            self.temp_dir, "video.avi"
        )

        self.capture_error = None
        self.audio_error = None
        self.stop_event.clear()

        audio_ok = self.start_audio()

        self.recording = True
        self.start_button.config(state="disabled")
        self.stop_button.config(state="normal")

        if audio_ok:
            self.set_status("Grabando pantalla y micrófono...")
        else:
            self.set_status("Grabando pantalla sin audio")

            messagebox.showwarning(
                "Audio no disponible",
                "No se pudo iniciar la entrada de audio.\n"
                "La grabación continuará sin sonido.\n\n"
                + str(self.audio_error)
            )

        self.capture_thread = threading.Thread(
            target=self.capture_screen,
            daemon=True
        )
        self.capture_thread.start()

    def capture_screen(self):
        writer = None

        try:
            with mss.mss() as screen:
                monitor = screen.monitors[1]

                width = max(
                    2,
                    int(monitor["width"] * SCREEN_SCALE)
                )
                height = max(
                    2,
                    int(monitor["height"] * SCREEN_SCALE)
                )

                width -= width % 2
                height -= height % 2

                fourcc = cv2.VideoWriter_fourcc(*"MJPG")

                writer = cv2.VideoWriter(
                    self.video_path,
                    fourcc,
                    FPS,
                    (width, height)
                )

                if not writer.isOpened():
                    raise RuntimeError(
                        "No se pudo crear el archivo de video."
                    )

                interval = 1.0 / FPS

                while not self.stop_event.is_set():
                    start_time = time.monotonic()

                    image = np.array(screen.grab(monitor))

                    frame = cv2.cvtColor(
                        image,
                        cv2.COLOR_BGRA2BGR
                    )

                    frame = cv2.resize(
                        frame,
                        (width, height),
                        interpolation=cv2.INTER_AREA
                    )

                    writer.write(frame)

                    elapsed = time.monotonic() - start_time
                    wait_time = max(0, interval - elapsed)

                    self.stop_event.wait(wait_time)

        except Exception as error:
            self.capture_error = str(error)
            self.stop_event.set()

        finally:
            if writer is not None:
                writer.release()

            self.root.after(
                0,
                self.capture_finished
            )

    def stop_recording(self):
        if not self.recording:
            return

        self.stop_button.config(state="disabled")
        self.set_status("Deteniendo grabación...")

        self.stop_event.set()
        self.close_audio()

    def capture_finished(self):
        if self.capture_error:
            self.recording = False
            self.close_audio()

            self.start_button.config(state="normal")
            self.stop_button.config(state="disabled")

            messagebox.showerror(
                "Error de grabación",
                self.capture_error
            )

            self.set_status("La grabación no pudo completarse")
            return

        self.set_status("Preparando video MP4...")

        threading.Thread(
            target=self.finalize_video,
            daemon=True
        ).start()

    def finalize_video(self):
        try:
            ffmpeg = find_ffmpeg()

            if not ffmpeg:
                raise RuntimeError(
                    "No se encontró ffmpeg.exe."
                )

            if not os.path.isfile(self.video_path):
                raise RuntimeError(
                    "No se encontró el video temporal."
                )

            command = [
                ffmpeg,
                "-y",
                "-i", self.video_path
            ]

            audio_exists = (
                self.audio_path is not None
                and os.path.isfile(self.audio_path)
                and os.path.getsize(self.audio_path) > 44
            )

            if audio_exists:
                command.extend([
                    "-i", self.audio_path,
                    "-map", "0:v:0",
                    "-map", "1:a:0",
                    "-c:a", "aac",
                    "-b:a", "64k",
                    "-shortest"
                ])
            else:
                command.extend(["-an"])

            command.extend([
                "-c:v", "libx264",
                "-preset", "ultrafast",
                "-crf", "28",
                "-pix_fmt", "yuv420p",
                "-r", str(FPS),
                "-movflags", "+faststart",
                self.output_path
            ])

            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                creationflags=getattr(
                    subprocess, "CREATE_NO_WINDOW", 0
                )
            )

            if result.returncode != 0:
                raise RuntimeError(
                    result.stderr[-2500:]
                    if result.stderr
                    else "FFmpeg no pudo crear el MP4."
                )

            self.root.after(
                0,
                self.finish_success
            )

        except Exception as error:
            self.root.after(
                0,
                lambda: self.finish_error(str(error))
            )

    def finish_success(self):
        self.recording = False

        self.start_button.config(state="normal")
        self.stop_button.config(state="disabled")

        self.set_status("¡Grabación guardada!")

        messagebox.showinfo(
            "La Pauta Capture",
            "Grabación guardada correctamente:\n\n"
            + self.output_path
        )

        if self.temp_dir:
            shutil.rmtree(
                self.temp_dir,
                ignore_errors=True
            )

        self.set_status("Listo para grabar")

    def finish_error(self, error):
        self.recording = False

        self.start_button.config(state="normal")
        self.stop_button.config(state="disabled")

        self.set_status("Error al guardar")

        messagebox.showerror(
            "Error al crear el MP4",
            error
        )


if __name__ == "__main__":
    root = tk.Tk()
    app = LaPautaCapture(root)
    root.mainloop()
