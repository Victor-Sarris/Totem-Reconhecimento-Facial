import cv2 as cv
import os

# nome da pessoa que será cadastrada
nome_pessoa = "Sarris" # Mude para o nome da pessoa que está na frente da câmera

# salvar as fotos
data_path = "dataset"
person_path = os.path.join(data_path, nome_pessoa)

if not os.path.exists(person_path):
    print(f"Criando pasta: {person_path}")
    os.makedirs(person_path)

# webcam = cv.VideoCapture(1) acessa a câmera da sua máquina

url_esp32 = "http://192.168.18.159/stream"
wevam = cv.VideoCapture(url_esp32)


count = 0

while True:
    verificador, frame = webcam.read()
    if not verificador:
        break

    cv.imshow("Captura de Rosto - Pressione 's' para salvar", frame)
    
    key = cv.waitKey(5)

    # se a tecla 's' for pressionada, salva a imagem
    if key == ord('s'):
        file_name = os.path.join(person_path, f'{count}.jpg')
        cv.imwrite(file_name, frame)
        print(f"Foto salva em: {file_name}")
        count += 1
    
    # se a tecla 'esc' for pressionada, sai do loop
    elif key == 27:
        break

print(f"{count} fotos salvas para {nome_pessoa}.")
webcam.release()
cv.destroyAllWindows()