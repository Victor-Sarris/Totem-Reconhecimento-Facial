import cv2 as cv
import mediapipe as mp

# inicializar o open cv e o mediapipe
webcam = cv.VideoCapture(0)  # ajuste o índice da câmera
solucao_reconhecimento = mp.solutions.face_detection
reconhecedor_rostos = solucao_reconhecimento.FaceDetection(min_detection_confidence=0.8)
desenho = mp.solutions.drawing_utils

while True:
    verificador, frame = webcam.read()
    if not verificador:
        break

    # converter para RGB
    frame_rgb = cv.cvtColor(frame, cv.COLOR_BGR2RGB)

    # processar reconhecimento
    lista_rostos = reconhecedor_rostos.process(frame_rgb)

    if lista_rostos.detections:
        for rosto in lista_rostos.detections:
            score = rosto.score[0]
            if score > 0.8:  # evita falsos positivos
                desenho.draw_detection(frame, rosto)
                cv.putText(frame, f"{int(score*100)}%", (50, 50),
                           cv.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

    cv.imshow("Webcam | Detectacao de Faces", frame)

    if cv.waitKey(5) == 27:  # tecla ESC
        break

webcam.release()
cv.destroyAllWindows()
