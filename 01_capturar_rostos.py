# Arquivo: 01_capturar_rostos.py
import cv2 as cv
import os

# Nome da pessoa que será cadastrada
nome_pessoa = "Victor" # Mude para o nome da pessoa que está na frente da câmera

# Diretório para salvar as fotos
data_path = "dataset"
person_path = os.path.join(data_path, nome_pessoa)

if not os.path.exists(person_path):
    print(f"Criando pasta: {person_path}")
    os.makedirs(person_path)

webcam = cv.VideoCapture(0)
count = 0

while True:
    verificador, frame = webcam.read()
    if not verificador:
        break

    # Mostra a imagem da webcam
    cv.imshow("Captura de Rosto - Pressione 's' para salvar", frame)
    
    # Espera por uma tecla
    key = cv.waitKey(5)

    # Se a tecla 's' for pressionada, salva a imagem
    if key == ord('s'):
        file_name = os.path.join(person_path, f'{count}.jpg')
        cv.imwrite(file_name, frame)
        print(f"Foto salva em: {file_name}")
        count += 1
    
    # Se a tecla ESC (27) for pressionada, sai do loop
    elif key == 27:
        break

print(f"{count} fotos salvas para {nome_pessoa}.")
webcam.release()
cv.destroyAllWindows()