import face_recognition
import pickle
import os
import cv2

# --- CONFIGURAÇÕES ---
dataset_path = "dataset/"
encoding_file = "encodings.pickle"
# ---------------------

known_encodings = []
known_names = []

print("[INFO] Iniciando processamento das imagens...")

# Varre todas as pastas dentro de 'dataset'
for nome_pessoa in os.listdir(dataset_path):
    pasta_pessoa = os.path.join(dataset_path, nome_pessoa)
    
    if not os.path.isdir(pasta_pessoa):
        continue

    print(f"[INFO] Processando: {nome_pessoa}")

    # Varre cada foto da pessoa
    for arquivo_imagem in os.listdir(pasta_pessoa):
        caminho_imagem = os.path.join(pasta_pessoa, arquivo_imagem)
        
        # Carrega a imagem e converte de BGR (OpenCV) para RGB (Dlib)
        imagem = cv2.imread(caminho_imagem)
        if imagem is None:
            continue
            
        rgb = cv2.cvtColor(imagem, cv2.COLOR_BGR2RGB)

        # Detecta rostos na imagem 
        boxes = face_recognition.face_locations(rgb, model="hog")

        # Gera os embeddings 
        encodings = face_recognition.face_encodings(rgb, boxes)

        # Guarda o encoding e o nome
        for encoding in encodings:
            known_encodings.append(encoding)
            known_names.append(nome_pessoa)

print("[INFO] Serializando encodings...")
data = {"encodings": known_encodings, "names": known_names}

with open(encoding_file, "wb") as f:
    f.write(pickle.dumps(data))

print(f"[SUCESSO] Arquivo '{encoding_file}' gerado com sucesso!")