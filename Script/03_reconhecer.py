import cv2
import face_recognition
import pickle
import numpy as np
import requests

# --- CONFIGURAÇÕES ---
url_esp32 = "http://192.168.18.159/stream" # Seu IP
encoding_file = "encodings.pickle"
# ---------------------

print("[INFO] Carregando encodings...")
data = pickle.loads(open(encoding_file, "rb").read())

print(f"[INFO] Conectando ao ESP32: {url_esp32}")
try:
    stream = requests.get(url_esp32, stream=True, timeout=5)
    bytes_buffer = bytes()
except Exception as e:
    print(f"[ERRO] Falha ao conectar: {e}")
    exit()

print("[INFO] Iniciando reconhecimento. Pressione 'q' para sair.")

# Chunk maior para garantir fluxo
for chunk in stream.iter_content(chunk_size=4096):
    bytes_buffer += chunk
    
    # Loop para decodificar frames do buffer
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
            # Decodifica a imagem
            frame = cv2.imdecode(np.frombuffer(jpg, dtype=np.uint8), cv2.IMREAD_COLOR)
            if frame is None: continue

            # --- OTIMIZAÇÃO PARA LABRADOR ---
            # Reduzimos o frame para 1/4 do tamanho para o reconhecimento ficar rápido
            small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
            rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

            # 1. Detecta rostos no frame pequeno
            face_locations = face_recognition.face_locations(rgb_small_frame)
            
            # 2. Codifica os rostos detectados
            face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)

            face_names = []
            for face_encoding in face_encodings:
                # Compara com os rostos conhecidos
                matches = face_recognition.compare_faces(data["encodings"], face_encoding, tolerance=0.5)
                name = "Desconhecido"

                # Se houver match, verifica qual é o mais parecido (menor distância)
                face_distances = face_recognition.face_distance(data["encodings"], face_encoding)
                best_match_index = np.argmin(face_distances)
                
                if matches[best_match_index]:
                    name = data["names"][best_match_index]

                face_names.append(name)
                
                # Feedback no terminal se encontrar alguém
                if name != "Desconhecido":
                    print(f"Reconhecido: {name}")

            # 3. Desenha os resultados no frame original (grande)
            for (top, right, bottom, left), name in zip(face_locations, face_names):
                # Escala de volta as coordenadas (vezes 4)
                top *= 4
                right *= 4
                bottom *= 4
                left *= 4

                # Desenha o quadrado
                cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
                
                # Desenha o nome
                cv2.rectangle(frame, (left, bottom - 35), (right, bottom), (0, 255, 0), cv2.FILLED)
                cv2.putText(frame, name, (left + 6, bottom - 6), cv2.FONT_HERSHEY_DUPLEX, 0.6, (255, 255, 255), 1)

            cv2.imshow("Reconhecimento Facial (Dlib)", frame)
            
            if cv2.waitKey(1) & 0xFF == ord('q'):
                exit()
                
        except Exception as e:
            pass