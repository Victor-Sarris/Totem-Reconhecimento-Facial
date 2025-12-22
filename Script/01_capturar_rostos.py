import cv2 as cv
import numpy as np
import requests
import os

# --- CONFIGURAÇÕES ---
nome_pessoa = "Sarris"
url_esp32 = "http://192.168.18.159/stream" 
# ---------------------

data_path = "dataset"
person_path = os.path.join(data_path, nome_pessoa)

if not os.path.exists(person_path):
    os.makedirs(person_path)

print(f"Conectando ao ESP32 em: {url_esp32}")

try:
    # Conecta no stream de dados bruto
    stream = requests.get(url_esp32, stream=True, timeout=5)
    
    if stream.status_code == 200:
        print("Conexão aceita! Iniciando captura...")
    else:
        print(f"Erro ao conectar: Código {stream.status_code}")
        exit()

    bytes_buffer = bytes()
    count = 0

    # Lê o stream em pedaços de 1024 bytes
    for chunk in stream.iter_content(chunk_size=1024):
        bytes_buffer += chunk
        
        # Procura os "marcadores" mágicos de início (0xffd8) e fim (0xffd9) de um JPEG
        a = bytes_buffer.find(b'\xff\xd8')
        b = bytes_buffer.find(b'\xff\xd9')
        
        if a != -1 and b != -1:
            # Recorta exatamente uma imagem JPEG do buffer
            jpg = bytes_buffer[a:b+2]
            bytes_buffer = bytes_buffer[b+2:] # Guarda o resto para a próxima volta
            
            # Decodifica a imagem da memória para o OpenCV
            frame = cv.imdecode(np.frombuffer(jpg, dtype=np.uint8), cv.IMREAD_COLOR)
            
            if frame is not None:
                cv.imshow("Captura Manual - 's' para salvar", frame)
                
                key = cv.waitKey(1) & 0xFF
                if key == ord("s"):
                    file_name = os.path.join(person_path, f"{count}.jpg")
                    cv.imwrite(file_name, frame)
                    print(f"✅ Foto salva: {file_name}")
                    count += 1
                elif key == 27: # ESC
                    break
            else:
                print("Aviso: Frame vazio recebido.")

except requests.exceptions.ConnectionError:
    print("ERRO FATAL: Não foi possível conectar ao ESP32.")
    print("1. Verifique se o IP está correto.")
    print("2. Verifique se o ESP32 está ligado e na mesma rede Wi-Fi.")
except Exception as e:
    print(f"Erro desconhecido: {e}")

print("Encerrando...")
cv.destroyAllWindows()