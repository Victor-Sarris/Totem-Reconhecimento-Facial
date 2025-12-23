import cv2 as cv
import mediapipe as mp
import pickle
import numpy as np
from deepface import DeepFace

# variaveis
rosto_reconhecido = None

# --- 1. CARREGAR DADOS DE RECONHECIMENTO ---
# Carregar os embeddings conhecidos do arquivo
with open("embeddings.pkl", "rb") as f:
    embeddings_conhecidos = pickle.load(f)

# Extrair nomes e a média dos embeddings para cada pessoa
nomes_conhecidos = list(embeddings_conhecidos.keys())
embeddings_medios_conhecidos = []
for nome in nomes_conhecidos:
    embeddings_medios_conhecidos.append(np.mean(embeddings_conhecidos[nome], axis=0))

# --- 2. INICIALIZAR WEBCAM E MEDIAPIPE ---
webcam = cv.VideoCapture(0) 
solucao_reconhecimento = mp.solutions.face_detection
reconhecedor_rostos = solucao_reconhecimento.FaceDetection(min_detection_confidence=0.7)
desenho = mp.solutions.drawing_utils

while True:
    verificador, frame = webcam.read()
    if not verificador:
        break

    # Obter altura e largura do frame para calcular as coordenadas
    altura, largura, _ = frame.shape
    
    # Converter para RGB 
    frame_rgb = cv.cvtColor(frame, cv.COLOR_BGR2RGB)

    # Processar reconhecimento de rostos
    lista_rostos = reconhecedor_rostos.process(frame_rgb)
    
    # 
    
    if lista_rostos.detections:
        for rosto in lista_rostos.detections:
            
            # --- 3. LÓGICA DE RECONHECIMENTO FACIAL ---
            
            # Pegar as coordenadas do rosto detectado
            bbox_data = rosto.location_data.relative_bounding_box
            x = int(bbox_data.xmin * largura)
            y = int(bbox_data.ymin * altura)
            w = int(bbox_data.width * largura)
            h = int(bbox_data.height * altura)

            x, y, w, h = max(0, x), max(0, y), max(0, w), max(0, h)

            # Recortar o rosto do frame 
            rosto_recortado = frame[y:y+h, x:x+w]

            nome = "Desconhecido" 
            
            if rosto_recortado.size != 0:
                try:
                    # Gerar o embedding para o rosto detectado na hora
                    embedding_atual = DeepFace.represent(rosto_recortado, model_name='Facenet', enforce_detection=False)[0]["embedding"]
                    
                    distancias = []
                    for emb_conhecido in embeddings_medios_conhecidos:
                        # Calculando a distância do embedding
                        dist = 1 - np.dot(embedding_atual, emb_conhecido) / (np.linalg.norm(embedding_atual) * np.linalg.norm(emb_conhecido))
                        distancias.append(dist)
                    
                    # Encontrar a menor distância e o índice correspondente
                    idx_melhor_match = np.argmin(distancias)
                    
                    # Se a menor distância for menor que um limiar, a pessoa foi reconhecida
                    if distancias[idx_melhor_match] < 0.4: # Limiar de decisão (posso ajustar futuramente)
                        nome = nomes_conhecidos[idx_melhor_match]
                        rosto_reconhecido = nome
                
                except Exception as e:
                    
                    # Se DeepFace não conseguir processar a imagem, continua como "Desconhecido"
                    pass

            # --- 4. EXIBIR O RESULTADO NA TELA ---
            
            # Desenhar um retângulo verde ao redor do rosto
            cv.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
            
            # Escrever o nome da pessoa reconhecida
            cv.putText(frame, nome, (x, y - 10), cv.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
            
            
    if(rosto_reconhecido):
        print(f'Reconhecimento facial feito: {nome}')
        break
    cv.imshow("Reconhecimento Facial em Tempo Real", frame)

    if cv.waitKey(5) == 27:  # tecla ESC
        break

# webcam.release()
# cv.destroyAllWindows()