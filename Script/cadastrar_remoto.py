import requests

# IP do Labrador
url = "http://192.168.18.149:5000/api/cadastrar_direto"

# Caminho da foto no seu computador
caminho_foto = "/dataset/Sarris" 
nome_cliente = "Yasmin"

print("Enviando foto para o Labrador...")
with open(caminho_foto, 'rb') as f:
    files = {'foto': f}
    data = {'nome': nome_cliente}
    response = requests.post(url, files=files, data=data)

print(response.json())