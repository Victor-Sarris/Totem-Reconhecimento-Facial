import requests
import os

# IP do Labrador 
url = "http://192.168.18.149:5000/api/cadastrar_direto"

# Caminho da PASTA com as fotos (Não precisa colocar o arquivo específico)
# O script faz a varredura na pasta e manda as imagens para o Labrador
pasta_imagens = "dataset/Sarris"

# Nome da pessoa que será cadastrada
nome_cliente = "Sarris" 

# inicio do script
if not os.path.exists(pasta_imagens):
    print(f"❌ Erro: A pasta '{pasta_imagens}' não foi encontrada.")
    exit()

arquivos = os.listdir(pasta_imagens)
fotos_validas = [f for f in arquivos if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
total = len(fotos_validas)

print(f"--- Iniciando envio em massa para: {nome_cliente} ---")
print(f"📂 Pasta: {pasta_imagens}")
print(f"📸 Total de fotos encontradas: {total}\n")

sucessos = 0

for i, arquivo in enumerate(fotos_validas):
    caminho_completo = os.path.join(pasta_imagens, arquivo)
    
    print(f"[{i+1}/{total}] Enviando {arquivo}...", end=" ")
    
    try:
        with open(caminho_completo, 'rb') as f:
            files = {'foto': f}
            data = {'nome': nome_cliente}
            
            # envia para o Labrador
            response = requests.post(url, files=files, data=data)
            
        if response.status_code == 201:
            print("✅ Sucesso!")
            sucessos += 1
        else:
            print(f"⚠️ Falha: {response.json().get('erro')}")
            
    except Exception as e:
        print(f"❌ Erro de conexão: {e}")

print(f"\n--- CONCLUÍDO! ---")
print(f"✅ {sucessos} fotos processadas e salvas no banco de dados do Labrador.")