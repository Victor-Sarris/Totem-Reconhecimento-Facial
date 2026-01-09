import cv2 as cv
import numpy as np
import requests
import os

#  config
nome_pessoa = "Sarris"
url_esp32 = "http://192.168.18.159/stream" 


data_path = "dataset"
person_path = os.path.join(data_path, nome_pessoa)

if not os.path.exists(person_path):
    os.makedirs(person_path)

print(f"Conectando ao ESP32 em: {url_esp32}")

try:
    stream = requests.get(url_esp32, stream=True, timeout=5)
    bytes_buffer = bytes()
    count = 0

    print("Conexão aceita! Pressione 's' para salvar e 'ESC' para sair.")

    for chunk in stream.iter_content(chunk_size=4096):
        bytes_buffer += chunk
        
        # loop para processar tudo que estiver no buffer
        while True:
            a = bytes_buffer.find(b'\xff\xd8')
            b = bytes_buffer.find(b'\xff\xd9')
            
            if a == -1 or b == -1:
                break
                
            # se o buffer tiver cheio, faz a limpeza do mesmo
            if b < a:
                bytes_buffer = bytes_buffer[b+2:]
                continue # limpa o buffer e tenta novamente

            jpg = bytes_buffer[a:b+2]
            bytes_buffer = bytes_buffer[b+2:] # remove a imagem já processada
            
            # tenta decodificar
            try:
                frame = cv.imdecode(np.frombuffer(jpg, dtype=np.uint8), cv.IMREAD_COLOR)
                
                if frame is not None:
                    # redimensiona a imagem para menor processamento
                    # frame = cv.resize(frame, (640, 480))
                    
                    cv.imshow("Captura Manual", frame)
                    
                    key = cv.waitKey(1) & 0xFF
                    if key == ord("s"):
                        file_name = os.path.join(person_path, f"{count}.jpg")
                        cv.imwrite(file_name, frame)
                        print(f"✅ Foto salva: {file_name}")
                        count += 1
                    elif key == 27: # ESC
                        exit()
            except Exception as e:
                pass # se der erro num frame específico, apenas ignora e vai pro próximo

except Exception as e:
    print(f"Erro: {e}")