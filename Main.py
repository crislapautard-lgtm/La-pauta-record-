import cv2, numpy as np, mss, time, os, threading, subprocess, sys
import sounddevice as sd
import soundfile as sf
from datetime import datetime
print("LA PAUTA CAPTURE - PC DE CARTON")
print("")
hostapis = sd.query_hostapis()
for i, api in enumerate(hostapis):
    print(f"[{i}] {api['name']}")
print("")
try:
    api_elegida = int(input("Elige el NUMERO del DRIVER (0=ASIO, 1=WASAPI, etc): "))
    api_info = hostapis[api_elegida]
except:
    api_info = hostapis[0]
print("")
print(f"--- TARJETAS CON {api_info['name']} ---")
for idx in api_info['devices']:
    d = sd.query_devices(idx)
    if d['max_input_channels'] > 0:
        print(f"[{idx}] {d['name']}")
print("")
eleccion = int(input("Escribe el NUMERO de tu tarjeta: "))
device_info = sd.query_devices(eleccion)
print(f"Listo: {device_info['name']} por {api_info['name']}")
samplerate = 44100
canales = 1
FPS = 8
ESCALA = 0.5
CARPETA = os.path.join(os.path.expanduser("~"), "Videos", "La Pauta Capture")
os.makedirs(CARPETA, exist_ok=True)
base = os.path.join(CARPETA, f"pauta_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}")
video_solo = base + "_video.mp4"
audio_solo = base + "_audio.wav"
final = base + ".mp4"
grabando_audio = True
audio_data = []
def grabar_audio():
    try:
        with sd.InputStream(samplerate=samplerate, channels=canales, device=eleccion, dtype='int16') as stream:
            while grabando_audio:
                data, _ = stream.read(1024)
                audio_data.append(data.copy())
    except Exception as e:
        print(f"Error: {e} - Prueba con WASAPI")
hilo = threading.Thread(target=grabar_audio, daemon=True)
hilo.start()
print("Grabando... Presiona 'q' para parar")
with mss.mss() as sct:
    monitor = sct.monitors[1]
    ancho = int(monitor["width"] * ESCALA)
    alto = int(monitor["height"] * ESCALA)
    writer = cv2.VideoWriter(video_solo, cv2.VideoWriter_fourcc(*"mp4v"), FPS, (ancho, alto))
    while True:
        img = np.array(sct.grab(monitor))
        frame = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
        frame = cv2.resize(frame, (ancho, alto))
        writer.write(frame)
        cv2.imshow("LA PAUTA CAPTURE - Q para parar", cv2.resize(frame, (320, 180)))
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break
writer.release()
cv2.destroyAllWindows()
grabando_audio = False
time.sleep(0.5)
print("Uniendo video + audio...")
if audio_data:
    audio_np = np.concatenate(audio_data, axis=0)
    sf.write(audio_solo, audio_np, samplerate)
    ffmpeg = os.path.join(os.path.dirname(sys.executable), "ffmpeg.exe") if getattr(sys, 'frozen', False) else "ffmpeg"
    subprocess.run([ffmpeg, "-y", "-i", video_solo, "-i", audio_solo, "-c:v", "copy", "-c:a", "aac", "-b:a", "64k", final], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    os.remove(video_solo)
    os.remove(audio_solo)
    print(f"LISTO! Guardado en: {final}")
else:
    print(f"Solo video: {video_solo}")
input("Enter para salir - LA PAUTA CAPTURE")
