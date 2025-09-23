from deepface import DeepFace
import os
import pickle

dataset_path = "dataset/"
embeddings_conhecidos = {}

for nome_pessoa in os.listdir(dataset_path):
    pasta_pessoa = os.path.join(dataset_path, nome_pessoa)
    if not os.path.isdir(pasta_pessoa):
        continue
    
    embeddings_pessoa = []
    for imagem_nome in os.listdir(pasta_pessoa):
        imagem_path = os.path.join(pasta_pessoa, imagem_nome)
        try:
            embedding_obj = DeepFace.represent(img_path=imagem_path, model_name='Facenet', enforce_detection=False)
            embeddings_pessoa.append(embedding_obj[0]["embedding"])
        except Exception as e:
            print(f"Não foi possível processar a imagem {imagem_path}: {e}")
    
    if embeddings_pessoa:
        embeddings_conhecidos[nome_pessoa] = embeddings_pessoa
        print(f"Embeddings gerados para {nome_pessoa}")

# salva o dicionário de embeddings em um arquivo
with open("embeddings.pkl", "wb") as f:
    pickle.dump(embeddings_conhecidos, f)

print("\nArquivo 'embeddings.pkl' criado com sucesso!")