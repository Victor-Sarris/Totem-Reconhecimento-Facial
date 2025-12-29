import cv2
import face_recognition
import pickle
import numpy as np
import requests

# --- CONFIGURAÇÕES ---
url_esp32 = "http://192.168.18.159/stream" # IP da espcam
encoding_file = "encodings.pickle"

print("[INFO] Carregando encodings...")
data = pickle.loads(open(encoding_file, "rb").read())

print(f"[INFO] Conectando ao ESP32: {url_esp32}")
try:
    stream = requests.get(url_esp32, stream=True, timeout=5)
    bytes_buffer = bytes()
except Exception as e:
    print(f"[ERRO] Falha ao conectar: {e}")
    exit()

print("[INFO] Sistema Iniciado. Aguardando rosto...")

# Variáveis de Controle de Estado
acesso_liberado = False
nome_liberado = ""
posicao_rosto = [] 

for chunk in stream.iter_content(chunk_size=4096):
    bytes_buffer += chunk
    
    while True:
        a = bytes_buffer.find(b'\xff\xd8')
        b = bytes_buffer.find(b'\xff\xd9')
        
        if a == -1 or b == -1:
            break
            
        if b < a:
            bytes_buffer = bytes_buffer[b+2:]
            continue

        jpg = bytes_buffer[a:b+2]
        bytes_buffer = bytes_buffer[b+2:]
        
        try:
            frame = cv2.imdecode(np.frombuffer(jpg, dtype=np.uint8), cv2.IMREAD_COLOR)
            if frame is None: continue

            # Se ainda NÃO liberou o acesso, continua procurando
            if not acesso_liberado:
                
                # Reduz para processar rápido (tamanho da imagem)
                small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
                rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

                face_locations = face_recognition.face_locations(rgb_small_frame)
                face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)

                for face_encoding, location in zip(face_encodings, face_locations):
                    matches = face_recognition.compare_faces(data["encodings"], face_encoding, tolerance=0.5)
                    name = "Desconhecido"

                    face_distances = face_recognition.face_distance(data["encodings"], face_encoding)
                    best_match_index = np.argmin(face_distances)
                    
                    if matches[best_match_index]:
                        name = data["names"][best_match_index]

                    # se reconheceu:
                    if name != "Desconhecido":
                        acesso_liberado = True
                        nome_liberado = name
                        posicao_rosto = location 
                        
                        # Imprime só uma vez no terminal
                        print(f"\n{'='*30}")
                        print(f"✅ ACESSO LIBERADO PARA: {name.upper()}")
                        print(f"{'='*30}\n")
                        print("Pressione 'q' ou 'ESC' para encerrar o sistema.")

            # --- DESENHO NA TELA (INTERFACE) ---
            
            # Se o acesso já foi liberado...
            if acesso_liberado:
                # barra verde no topo da janela
                cv2.rectangle(frame, (0, 0), (frame.shape[1], 50), (0, 255, 0), -1)
                texto = f"ACESSO LIBERADO: {nome_liberado}"
                cv2.putText(frame, texto, (10, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 2)
                

            # Se ainda não liberou, desenha "Aguardando..."
            else:
                cv2.rectangle(frame, (0, 0), (frame.shape[1], 30), (0, 0, 255), -1)
                cv2.putText(frame, "BLOQUEADO - APROXIME O ROSTO", (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

            cv2.imshow("Sistema de Controle de Acesso", frame)
            
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q') or key == 27: # 'q' ou ESC para sair
                print("[INFO] Sistema encerrado pelo usuário.")
                exit()
                
        except Exception as e:
            pass