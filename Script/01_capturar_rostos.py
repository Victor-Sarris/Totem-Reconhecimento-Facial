import cv2 as cv
import os
import time

# --- CONFIGURAÇÕES ---
nome_pessoa = "Sarris"  # Nome da pasta
url_esp32 = "http://192.168.18.159/stream" # Seu IP correto
# ---------------------

data_path = "dataset"
person_path = os.path.join(data_path, nome_pessoa)

if not os.path.exists(person_path):
    print(f"Criando pasta: {person_path}")
    os.makedirs(person_path)

print(f"Tentando conectar em: {url_esp32}")
print("Aguarde... isso pode levar alguns segundos.")

webcam = cv.VideoCapture(url_esp32)

# Aumenta o tamanho do buffer para evitar travamentos no WiFi
webcam.set(cv.CAP_PROP_BUFFERSIZE, 2)

if not webcam.isOpened():
    print("ERRO CRÍTICO: Não foi possível conectar ao ESP32.")
    print("Verifique se o IP está correto e se o ESP32 está ligado.")
    exit()

print("Conectado! Abrindo janela...")
count = 0
erros_consecutivos = 0

while True:
    verificador, frame = webcam.read()

    # Se falhar ao ler o frame (comum em WiFi)
    if not verificador:
        erros_consecutivos += 1
        print(f"Aviso: Frame perdido/corrompido ({erros_consecutivos})")
        
        # Se falhar 100 vezes seguidas, aí sim desistimos
        if erros_consecutivos > 100:
            print("Muitos erros de conexão. Encerrando.")
            break
        
        time.sleep(0.1) # Espera um pouquinho e tenta de novo
        continue # Volta para o começo do loop

    # Se leu com sucesso, zera o contador de erros
    erros_consecutivos = 0

    # Redimensionar para ficar mais leve no VNC (Opcional, mas ajuda no Labrador)
    # frame = cv.resize(frame, (640, 480))

    cv.imshow("Captura - Pressione 's' para salvar", frame)

    key = cv.waitKey(1) & 0xFF

    if key == ord("s"):
        file_name = os.path.join(person_path, f"{count}.jpg")
        cv.imwrite(file_name, frame)
        print(f"✅ Foto salva: {file_name}")
        count += 1

    elif key == 27: # ESC
        print("Encerrando captura...")
        break

print(f"Total: {count} fotos salvas para {nome_pessoa}.")
webcam.release()
cv.destroyAllWindows()