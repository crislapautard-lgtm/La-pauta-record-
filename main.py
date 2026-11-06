
import os
import sys
import time
import shutil
import tempfile
import threading
import subprocess
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

import numpy as np
import cv2
import mss
import sounddevice as sd
import soundfile as sf
import soundcard as sc


APP_NAME = "LA PAUTA CAPTURE STUDIO"

FPS = 6
SCREEN_SCALE = 0.35
AUDIO_RATE = 48000
OUTPUT_RATE = 22050


def find_ffmpeg():
    paths = []

    if getattr(sys, "frozen", False):
        paths.extend([
            os.path.join(sys._MEIPASS, "ffmpeg.exe"),
            os.path.join(os.path.dirname(sys.executable), "ffmpeg.exe")
        ])

    paths.append(
        os.path.join(os.path.dirname(os.path.abspath(__file__)),
                     "ffmpeg.exe")
    )

    for path in paths:
        if os.path.isfile(path):
            return path

    return shutil.which("ffmpeg")


class LaPautaCapture:

    def __init__(self, root):
        self.root = root
        self.root.title(APP_NAME)
        self.root.geometry("680x510")
        self.root.resizable(False, False)
        self.root.configure(bg="#111418")

        self.recording = False
        self.stop_event = threading.Event()

        self.capture_thread = None
        self.loopback_thread = None

        self.input_stream = None
        self.input_file = None
        self.loopback_file = None

        self.input_path = None
        self.loopback_path = None
        self.video_path = None
        self.output_path = None
        self.temp_dir = None

        self.capture_error = None
        self.audio_error = None
        self.loopback_error = None

        self.input_devices = {}
        self.loopback_devices = {}

        self.create_interface()
        self.refresh_devices()

        self.root.protocol("WM_DELETE_WINDOW", self.close_app)

    # --------------------------------------------------
    # INTERFAZ
    # --------------------------------------------------

    def create_interface(self):

        style = ttk.Style()
        style.theme_use("clam")

        style.configure(
            "Dark.TCombobox",
            fieldbackground="#20262d",
            background="#20262d",
            foreground="#ffffff",
            arrowcolor="#42d6c5",
            bordercolor="#303942",
            lightcolor="#303942",
            darkcolor="#303942",
            padding=7
        )

        style.map(
            "Dark.TCombobox",
            fieldbackground=[("readonly", "#20262d")],
            foreground=[("readonly", "#ffffff")]
        )

        header = tk.Frame(self.root, bg="#111418")
        header.pack(fill="x", padx=25, pady=(17, 8))

        tk.Label(
            header,
            text="LA PAUTA",
            font=("Arial", 24, "bold"),
            fg="#42d6c5",
            bg="#111418"
        ).pack(anchor="w")

        tk.Label(
            header,
            text="CAPTURE STUDIO  /  WINDOWS",
            font=("Arial", 9, "bold"),
            fg="#aab3bb",
            bg="#111418"
        ).pack(anchor="w")

        tk.Frame(
            self.root,
            bg="#303942",
            height=1
        ).pack(fill="x", padx=25, pady=8)

        self.create_device_panel()

        info = tk.Frame(self.root, bg="#191e24")
        info.pack(fill="x", padx=25, pady=(15, 10))

        tk.Label(
            info,
            text="CONFIGURACIÓN DE GRABACIÓN",
            font=("Arial", 9, "bold"),
            fg="#42d6c5",
            bg="#191e24"
        ).pack(anchor="w", padx=13, pady=(10, 5))

        tk.Label(
            info,
            text="VIDEO  6 FPS  |  ESCALA 35%  |  COLOR NORMAL",
            font=("Arial", 9),
            fg="#d4d9df",
            bg="#191e24"
        ).pack(anchor="w", padx=13, pady=3)

        tk.Label(
            info,
            text="AUDIO  48 kHz CAPTURA  |  22.05 kHz MP4",
            font=("Arial", 9),
            fg="#d4d9df",
            bg="#191e24"
        ).pack(anchor="w", padx=13, pady=(3, 10))

        buttons = tk.Frame(self.root, bg="#111418")
        buttons.pack(pady=10)

        self.start_button = tk.Button(
            buttons,
            text="●  INICIAR GRABACIÓN",
            font=("Arial", 11, "bold"),
            bg="#42d6c5",
            fg="#101719",
            activebackground="#65e4d6",
            relief="flat",
            width=25,
            height=2,
            cursor="hand2",
            command=self.start_recording
        )
        self.start_button.pack(pady=5)

        self.stop_button = tk.Button(
            buttons,
            text="■  DETENER Y GUARDAR",
            font=("Arial", 10, "bold"),
            bg="#303942",
            fg="#ffffff",
            activebackground="#454e58",
            relief="flat",
            width=25,
            height=2,
            state="disabled",
            command=self.stop_recording
        )
        self.stop_button.pack(pady=5)

        self.status = tk.Label(
            self.root,
            text="● LISTO PARA GRABAR",
            font=("Arial", 10, "bold"),
            fg="#42d6c5",
            bg="#111418"
        )
        self.status.pack(pady=8)

        tk.Label(
            self.root,
            text="LA PAUTA AUDIO SYSTEM",
            font=("Arial", 8),
            fg="#606b75",
            bg="#111418"
        ).pack(side="bottom", pady=8)

    def create_device_panel(self):

        panel = tk.Frame(self.root, bg="#191e24")
        panel.pack(fill="x", padx=25, pady=5)

        tk.Label(
            panel,
            text="DISPOSITIVOS DE AUDIO",
            font=("Arial", 10, "bold"),
            fg="#42d6c5",
            bg="#191e24"
        ).pack(anchor="w", padx=13, pady=(10, 8))

        # SALIDA DE WINDOWS

        tk.Label(
            panel,
            text="AUDIO DEL PC / DAW (WASAPI LOOPBACK)",
            font=("Arial", 8, "bold"),
            fg="#dce2e8",
            bg="#191e24"
        ).pack(anchor="w", padx=13)

        self.loopback_combo = ttk.Combobox(
            panel,
            state="readonly",
            style="Dark.TCombobox",
            width=75
        )
        self.loopback_combo.pack(
            fill="x", padx=13, pady=(4, 10)
        )

        # ENTRADA DE AUDIO

        tk.Label(
            panel,
            text="MICRÓFONO / INTERFAZ / ENTRADA",
            font=("Arial", 8, "bold"),
            fg="#dce2e8",
            bg="#191e24"
        ).pack(anchor="w", padx=13)

        self.input_combo = ttk.Combobox(
            panel,
            state="readonly",
            style="Dark.TCombobox",
            width=75
        )
        self.input_combo.pack(
            fill="x", padx=13, pady=(4, 10)
        )

        self.refresh_button = tk.Button(
            panel,
            text="↻ ACTUALIZAR DISPOSITIVOS",
            font=("Arial", 8, "bold"),
            bg="#303942",
            fg="#ffffff",
            activebackground="#454e58",
            relief="flat",
            cursor="hand2",
            command=self.refresh_devices
        )
        self.refresh_button.pack(
            anchor="e", padx=13, pady=(0, 10)
        )

    # --------------------------------------------------
    # DETECTAR DISPOSITIVOS
    # --------------------------------------------------

    def refresh_devices(self):

        self.input_devices.clear()
        self.loopback_devices.clear()

        input_names = ["No grabar entrada"]
        loopback_names = ["No grabar audio del PC"]

        try:
            devices = sd.query_devices()

            default_input = None

            try:
                default_input = sd.default.device[0]
            except Exception:
                pass

            for index, device in enumerate(devices):

                channels = int(device["max_input_channels"])

                if channels > 0:
                    name = f"{index} - {device['name']}"

                    self.input_devices[name] = {
                        "index": index,
                        "channels": channels
                    }

                    input_names.append(name)

                    if index == default_input:
                        self.default_input_name = name

        except Exception as error:
            messagebox.showwarning(
                "Entradas de audio",
                str(error)
            )

        try:
            microphones = sc.all_microphones(
                include_loopback=True
            )

            default_speaker = None

            try:
                default_speaker = sc.default_speaker().name
            except Exception:
                pass

            for microphone in microphones:

                try:
                    if microphone.isloopback:

                        name = microphone.name

                        if name in self.loopback_devices:
                            name += f" ({len(loopback_names)})"

                        self.loopback_devices[name] = microphone
                        loopback_names.append(name)

                except Exception:
                    continue

            self.default_loopback_name = None

            if default_speaker:
                for name, microphone in self.loopback_devices.items():
                    if microphone.name == default_speaker:
                        self.default_loopback_name = name
                        break

        except Exception as error:
            self.loopback_error = str(error)

        self.input_combo["values"] = input_names
        self.loopback_combo["values"] = loopback_names

        self.input_combo.current(0)
        self.loopback_combo.current(0)

        if hasattr(self, "default_input_name"):
            self.input_combo.set(self.default_input_name)

        if self.default_loopback_name:
            self.loopback_combo.set(
                self.default_loopback_name
            )

        if not self.loopback_devices:
            self.set_status(
                "No se detectaron salidas Loopback"
            )
        else:
            self.set_status(
                f"Dispositivos detectados: "
                f"{len(self.input_devices)} entradas / "
                f"{len(self.loopback_devices)} salidas"
            )

    # --------------------------------------------------
    # GRABACIÓN DE ENTRADA
    # --------------------------------------------------

    def start_input_audio(self):

        selected = self.input_combo.get()

        if selected not in self.input_devices:
            return False

        device = self.input_devices[selected]

        channels = min(2, device["channels"])

        # Comprobar frecuencia compatible

        rate = AUDIO_RATE

        try:
            sd.check_input_settings(
                device=device["index"],
                channels=channels,
                samplerate=rate
            )
        except Exception:
            rate = 44100

            sd.check_input_settings(
                device=device["index"],
                channels=channels,
                samplerate=rate
            )

        self.input_path = os.path.join(
            self.temp_dir,
            "entrada.wav"
        )

        self.input_file = sf.SoundFile(
            self.input_path,
            mode="w",
            samplerate=rate,
            channels=channels,
            subtype="PCM_16"
        )

        def callback(indata, frames, timing, status):

            if self.stop_event.is_set():
                return

            try:
                self.input_file.write(indata)
            except Exception as error:
                self.audio_error = str(error)
                self.stop_event.set()

        self.input_stream = sd.InputStream(
            device=device["index"],
            samplerate=rate,
            channels=channels,
            dtype="float32",
            callback=callback
        )

        self.input_stream.start()

        return True

    # --------------------------------------------------
    # GRABACIÓN DE AUDIO DEL PC
    # --------------------------------------------------

    def start_loopback_audio(self):

        selected = self.loopback_combo.get()

        if selected not in self.loopback_devices:
            return False

        microphone = self.loopback_devices[selected]

        self.loopback_path = os.path.join(
            self.temp_dir,
            "audio_pc.wav"
        )

        ready = threading.Event()

        def loopback_worker():

            try:
                with sf.SoundFile(
                    self.loopback_path,
                    mode="w",
                    samplerate=AUDIO_RATE,
                    channels=2,
                    subtype="PCM_16"
                ) as audio_file:

                    with microphone.recorder(
                        samplerate=AUDIO_RATE,
                        channels=2
                    ) as recorder:

                        ready.set()

                        while not self.stop_event.is_set():

                            data = recorder.record(
                                numframes=2048
                            )

                            if data is None or len(data) == 0:
                                continue

                            audio_file.write(data)

            except Exception as error:
                self.loopback_error = str(error)
                ready.set()

        self.loopback_thread = threading.Thread(
            target=loopback_worker,
            daemon=True
        )

        self.loopback_thread.start()

        ready.wait(timeout=5)

        if self.loopback_error:
            return False

        return True

    # --------------------------------------------------
    # INICIAR
    # --------------------------------------------------

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
                "FFmpeg",
                "No se encontró ffmpeg.exe."
            )
            return

        self.output_path = output

        self.temp_dir = tempfile.mkdtemp(
            prefix="LaPautaCapture_"
        )

        self.video_path = os.path.join(
            self.temp_dir,
            "video.avi"
        )

        self.input_path = None
        self.loopback_path = None

        self.audio_error = None
        self.loopback_error = None
        self.capture_error = None

        self.stop_event.clear()

        audio_messages = []

        try:
            if self.input_combo.get() in self.input_devices:
                self.start_input_audio()
        except Exception as error:
            self.audio_error = str(error)
            audio_messages.append(
                "Entrada: " + str(error)
            )

        try:
            if self.loopback_combo.get() in self.loopback_devices:
                if not self.start_loopback_audio():
                    audio_messages.append(
                        "Audio del PC: " +
                        str(self.loopback_error)
                    )
        except Exception as error:
            self.loopback_error = str(error)
            audio_messages.append(
                "Audio del PC: " + str(error)
            )

        self.recording = True

        self.start_button.config(state="disabled")
        self.stop_button.config(
            state="normal",
            bg="#d94b50"
        )

        if audio_messages:
            self.set_status(
                "Grabando con audio parcialmente disponible"
            )
        else:
            self.set_status(
                "● GRABANDO PANTALLA Y AUDIO"
            )

        if audio_messages:
            messagebox.showwarning(
                "Aviso de audio",
                "\n\n".join(audio_messages) +
                "\n\nLa grabación de pantalla continuará."
            )

        self.capture_thread = threading.Thread(
            target=self.capture_screen,
            daemon=True
        )

        self.capture_thread.start()

    # --------------------------------------------------
    # CAPTURA DE PANTALLA
    # --------------------------------------------------

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

                fourcc = cv2.VideoWriter_fourcc(
                    *"MJPG"
                )

                writer = cv2.VideoWriter(
                    self.video_path,
                    fourcc,
                    FPS,
                    (width, height)
                )

                if not writer.isOpened():
                    raise RuntimeError(
                        "No se pudo crear el video temporal."
                    )

                interval = 1.0 / FPS

                while not self.stop_event.is_set():

                    start_time = time.monotonic()

                    image = np.array(
                        screen.grab(monitor)
                    )

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

                    elapsed = (
                        time.monotonic() - start_time
                    )

                    self.stop_event.wait(
                        max(0, interval - elapsed)
                    )

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

    # --------------------------------------------------
    # DETENER AUDIO
    # --------------------------------------------------

    def close_audio(self):

        if self.input_stream is not None:

            try:
                self.input_stream.stop()
            except Exception:
                pass

            try:
                self.input_stream.close()
            except Exception:
                pass

            self.input_stream = None

        if self.input_file is not None:

            try:
                self.input_file.close()
            except Exception:
                pass

            self.input_file = None

        if self.loopback_thread is not None:

            self.loopback_thread.join(timeout=4)

            if self.loopback_thread.is_alive():
                self.loopback_error = (
                    "El hilo de audio del PC no terminó a tiempo."
                )

            self.loopback_thread = None

    def stop_recording(self):

        if not self.recording:
            return

        self.stop_button.config(state="disabled")

        self.set_status(
            "DETENIENDO GRABACIÓN..."
        )

        self.stop_event.set()

    # --------------------------------------------------
    # FINALIZAR CAPTURA
    # --------------------------------------------------

    def capture_finished(self):

        self.close_audio()

        if self.capture_error:

            self.recording = False

            self.start_button.config(state="normal")
            self.stop_button.config(state="disabled")

            messagebox.showerror(
                "Error de grabación",
                self.capture_error
            )

            self.set_status("Error de captura")
            return

        self.set_status(
            "PREPARANDO VIDEO Y MEZCLANDO AUDIO..."
        )

        threading.Thread(
            target=self.finalize_video,
            daemon=True
        ).start()

    # --------------------------------------------------
    # CREAR MP4 Y MEZCLAR AUDIO
    # --------------------------------------------------

    def finalize_video(self):

        try:
            ffmpeg = find_ffmpeg()

            if not ffmpeg:
                raise RuntimeError(
                    "No se encontró FFmpeg."
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

            audio_inputs = []

            for path in [
                self.loopback_path,
                self.input_path
            ]:

                if (
                    path
                    and os.path.isfile(path)
                    and os.path.getsize(path) > 44
                ):

                    audio_inputs.append(path)

            for path in audio_inputs:
                command.extend(["-i", path])

            if len(audio_inputs) == 2:

                filter_complex = (
                    "[1:a]aresample=22050,"
                    "aformat=channel_layouts=mono[a1];"
                    "[2:a]aresample=22050,"
                    "aformat=channel_layouts=mono[a2];"
                    "[a1][a2]amix=inputs=2:"
                    "duration=longest:"
                    "dropout_transition=2,"
                    "alimiter=limit=0.95[aout]"
                )

                command.extend([
                    "-filter_complex",
                    filter_complex,
                    "-map", "0:v:0",
                    "-map", "[aout]"
                ])

            elif len(audio_inputs) == 1:

                filter_complex = (
                    "[1:a]aresample=22050,"
                    "aformat=channel_layouts=mono[aout]"
                )

                command.extend([
                    "-filter_complex",
                    filter_complex,
                    "-map", "0:v:0",
                    "-map", "[aout]"
                ])

            else:
                command.extend([
                    "-map", "0:v:0",
                    "-an"
                ])

            command.extend([
                "-c:v", "libx264",
                "-preset", "ultrafast",
                "-crf", "28",
                "-pix_fmt", "yuv420p",
                "-r", str(FPS),
                "-c:a", "aac",
                "-b:a", "96k",
                "-shortest",
                "-movflags", "+faststart",
                self.output_path
            ])

            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                creationflags=getattr(
                    subprocess,
                    "CREATE_NO_WINDOW",
                    0
                )
            )

            if result.returncode != 0:
                raise RuntimeError(
                    result.stderr[-3000:]
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

    # --------------------------------------------------
    # RESULTADOS
    # --------------------------------------------------

    def finish_success(self):

        self.recording = False

        self.start_button.config(state="normal")

        self.stop_button.config(
            state="disabled",
            bg="#303942"
        )

        messagebox.showinfo(
            "LA PAUTA CAPTURE",
            "¡Grabación guardada!\n\n" +
            self.output_path
        )

        if self.temp_dir:
            shutil.rmtree(
                self.temp_dir,
                ignore_errors=True
            )

        self.set_status(
            "● LISTO PARA GRABAR"
        )

    def finish_error(self, error):

        self.recording = False

        self.start_button.config(state="normal")

        self.stop_button.config(
            state="disabled",
            bg="#303942"
        )

        self.set_status(
            "ERROR AL GUARDAR"
        )

        messagebox.showerror(
            "Error al crear el MP4",
            error
        )

    def set_status(self, message):

        self.status.config(text=message)

    def close_app(self):

        if self.recording:

            if not messagebox.askyesno(
                "Salir",
                "Hay una grabación activa. ¿Deseas detenerla?"
            ):
                return

            self.stop_event.set()
            self.root.destroy()

        else:
            self.root.destroy()


if __name__ == "__main__":

    root = tk.Tk()

    app = LaPautaCapture(root)

    root.mainloop()
