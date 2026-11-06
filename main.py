import cv2, numpy as np, mss, time, os, threading, subprocess, sys
import sounddevice as sd
import soundfile as sf
from datetime import datetime

print("LA PAUTA CAPTURE - CALIDAD SUAVE - PC DE CARTON 4GB RAM")
print("")

hostapis = sd.query_hostapis()
print("=== DRIVERS DE AUDIO ===")
for i, api in enumerate(hostapis):
    print(f"[{i}] {api['name']}")
print("")

try:
    api_elegida = int(input("Elige el NUMERO del DRIVER (0=ASIO, 1=WASAPI, 2=MME, 3=DirectSound, 4=WDM-KS): "))
    api_info = hostapis[api_elegida]
except:
    api_info = hostapis[0]
    print(f"Usando: {api_info['name']}")

print("")
print(f"--- TARJETAS CON {api_info['name']} ---")
tarjetas = []
for idx in api_info['devices']:
    d = sd.query_devices(idx)
    if d['max_input_channels'] > 0:
        print(f"[{idx}] {d['name']}")
        tarjetas.append(idx)

if not tarjetas:
    print("Ese driver no tiene tarjetas, buscando WASAPI...")
    for api in hostapis:
        if "WASAPI" in api['name']:
            api_info = api
            break
    for idx in api_info['devices']:
        d = sd.query_devices(idx)
        if d['max_input_channels'] > 0:
            print(f"[{idx}] {d['name']}")
            tarjetas.append(idx)

print("")
eleccion = int(input("Escribe el NUMERO de tu tarjeta: "))
device_info = sd.query_devices(eleccion)
print(f"Listo: {device_info['name']} por {api_info['name']}")

samplerate = 22050
canales = 1
FPS = 6
ESCALA = 0.35
DTYPE_AUDIO = 'int8'

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
        with sd.InputStream(samplerate=samplerate, channels=canales, device=eleccion, dtype=DTYPE_AUDIO, blocksize=512) as stream:
            while grabando_audio:
                data, _ = stream.read(512)
                audio_data.append(data.copy())
    except Exception as e:
        print(f"Error: {e} - Probando driver por defecto...")
        try:
            with sd.InputStream(samplerate=samplerate, channels=canales, dtype=DTYPE_AUDIO, blocksize=512) as stream:
                while grabando_audio:
                    data, _ = stream.read(512)
                    audio_data.append(data.copy())
        except Exception as e2:
            print(f"Sin audio: {e2}")

hilo = threading.Thread(target=grabar_audio, daemon=True)
hilo.start()

print("Grabando en CALIDAD SUAVE... Presiona 'q' para parar")
print("6 FPS / 35% pantalla / Audio 8 BITS - No fuerza la PC")

with mss.mss() as sct:
    monitor = sct.monitors[1]
    ancho = int(monitor["width"] * ESCALA)
    alto = int(monitor["height"] * ESCALA)
    ancho = ancho - (ancho % 2)
    alto = alto - (alto % 2)
    print(f"Grabando a {ancho}x{alto} - Calidad suave")
    writer = cv2.VideoWriter(video_solo, cv2.VideoWriter_fourcc(*"mp4v"), FPS, (ancho, alto))
    ultimo_tiempo = time.time()
    intervalo = 1.0 / FPS
    while True:
        ahora = time.time()
        espera = intervalo - (ahora - ultimo_tiempo)
        if espera > 0:
            time.sleep(espera)
        ultimo_tiempo = time.time()
        img = np.array(sct.grab(monitor))
        frame = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
        frame = cv2.resize(frame, (ancho, alto), interpolation=cv2.INTER_NEAREST)
        writer.write(frame)
        cv2.imshow("LA PAUTA - Q para parar", cv2.resize(frame, (256, 144)))
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break
writer.release()
cv2.destroyAllWindows()

grabando_audio = False
time.sleep(0.5)
print("Uniendo video + audio...")

if audio_data:
    audio_np = np.concatenate(audio_data, axis=0)
    sf.write(audio_solo, audio_np, samplerate, subtype='PCM_U8')
    ffmpeg = os.path.join(os.path.dirname(sys.executable), "ffmpeg.exe") if getattr(sys, 'frozen', False) else "ffmpeg"
    subprocess.run([ffmpeg, "-y", "-i", video_solo, "-i", audio_solo, "-c:v", "libx264", "-crf", "30", "-preset", "ultrafast", "-c:a", "aac", "-b:a", "32k", final], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    os.remove(video_solo)
    os.remove(audio_solo)
    print(f"LISTO! Guardado en: {final}")
else:
    print(f"Solo video: {video_solo}")

input("Enter para salir - LA PAUTA CAPTURE")
