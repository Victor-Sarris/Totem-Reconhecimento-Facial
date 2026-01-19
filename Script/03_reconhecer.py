import cv2
import face_recognition
import pickle
import numpy as np
import threading
import time
import requests
from flask import Flask, Response, jsonify, request

ARQUIVO_DADOS = "encodings.pickle"
URL_CAMERA = "http://192.168.18.159/stream"
DELAY_RECONHECIMENTO = 10  
INTERVALO_SCAN_IA = 1.0   

app = Flask(__name__)

frame_atual = None
lista_encodings = []
lista_nomes = []
lock = threading.Lock()

class VideoStream:
    def __init__(self, src):
        self.stream = requests.get(src, stream=True, timeout=10)
        self.bytes_buffer = bytes()
        self.ultimo_frame_jpg = None
        self.rodando = False
        self.lock_video = threading.Lock()

    def start(self):
        self.rodando = True
        t = threading.Thread(target=self.update, args=())
        t.daemon = True
        t.start()
        return self

    def update(self):
        for chunk in self.stream.iter_content(chunk_size=4096):
            if not self.rodando: break
            self.bytes_buffer += chunk
            
            a = self.bytes_buffer.find(b'\xff\xd8')
            b = self.bytes_buffer.find(b'\xff\xd9')
            
            if a != -1 and b != -1:
                jpg = self.bytes_buffer[a:b+2]
                self.bytes_buffer = self.bytes_buffer[b+2:]
                
                with self.lock_video:
                    self.ultimo_frame_jpg = jpg

    def read(self):
        with self.lock_video:
            return self.ultimo_frame_jpg

    def stop(self):
        self.rodando = False

def carregar_dados():
    global lista_encodings, lista_nomes
    try:
        with open(ARQUIVO_DADOS, "rb") as f:
            data = pickle.load(f)
        lista_encodings = data["encodings"]
        lista_nomes = data["names"]
        print(f"[SISTEMA] Banco carregado: {len(lista_nomes)} usuarios.")
    except FileNotFoundError:
        print("[AVISO] Iniciando banco de dados vazio.")
        lista_encodings = []
        lista_nomes = []

def salvar_dados_pickle():
    global lista_encodings, lista_nomes
    with lock:
        data = {"encodings": lista_encodings, "names": lista_nomes}
        with open(ARQUIVO_DADOS, "wb") as f:
            f.write(pickle.dumps(data))

def loop_reconhecimento():
    global frame_atual, lista_encodings, lista_nomes
    
    ultimo_sucesso = 0
    ultimo_check_ia = 0
    nome_ultimo_detectado = ""
    
    print(f"[VIDEO] Iniciando buffer de vídeo: {URL_CAMERA}")
    
    videostream = VideoStream(URL_CAMERA).start()
    time.sleep(2.0) # Espera encher o buffer
    
    cv2.namedWindow("Totem Facial", cv2.WINDOW_NORMAL)
    
    while True:
        try:
            jpg_bytes = videostream.read()
            
            if jpg_bytes is None:
                time.sleep(0.01)
                continue
                
            frame = cv2.imdecode(np.frombuffer(jpg_bytes, dtype=np.uint8), cv2.IMREAD_COLOR)
            
            if frame is None: continue

            agora = time.time()
            em_cooldown = (agora - ultimo_sucesso) < DELAY_RECONHECIMENTO
            
            if not em_cooldown:
                if (agora - ultimo_check_ia) > INTERVALO_SCAN_IA:
                    ultimo_check_ia = agora
                    
                    small = cv2.resize(frame, (0,0), fx=0.5, fy=0.5)
                    rgb = cv2.cvtColor(small, cv2.COLOR_BGR2RGB)
                    
                    locs = face_recognition.face_locations(rgb)
                    
                    if locs and len(lista_encodings) > 0:
                        encs = face_recognition.face_encodings(rgb, locs)
                        
                        for encoding in encs:
                            with lock:
                                matches = face_recognition.compare_faces(lista_encodings, encoding, tolerance=0.5)
                                name = "Desconhecido"
                                if True in matches:
                                    first_match_index = matches.index(True)
                                    name = lista_nomes[first_match_index]
                            
                            if name != "Desconhecido":
                                print(f"== ACESSO LIBERADO: {name} ==")
                                ultimo_sucesso = agora
                                nome_ultimo_detectado = name
                                cv2.rectangle(frame, (0,0), (frame.shape[1], 60), (0,255,0), -1)
                                cv2.putText(frame, f"BEM-VINDO {name}", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (255,255,255), 2)
                else:
                    pass
            else:
                tempo = int(DELAY_RECONHECIMENTO - (agora - ultimo_sucesso))
                cv2.rectangle(frame, (0,0), (frame.shape[1], 60), (50,50,50), -1)
                cv2.putText(frame, f"LIBERADO: {nome_ultimo_detectado}", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,255,0), 2)
                cv2.putText(frame, f"Proximo: {tempo}s", (20, frame.shape[0]-20), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,255,255), 2)

            cv2.imshow("Totem Facial", frame)
            
            with lock:
                frame_atual = frame.copy()
            
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
                
        except Exception as e:
            time.sleep(1)
            
    videostream.stop()
    cv2.destroyAllWindows()

@app.route('/api/cadastrar_direto', methods=['POST'])
def cadastrar_direto():
    global lista_encodings, lista_nomes
    if 'foto' not in request.files or 'nome' not in request.form:
        return jsonify({"erro": "Faltou foto ou nome"}), 400
    
    arquivo = request.files['foto']
    nome = request.form['nome']
    
    npimg = np.frombuffer(arquivo.read(), np.uint8)
    img = cv2.imdecode(npimg, cv2.IMREAD_COLOR)
    rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    
    caixas = face_recognition.face_locations(rgb)
    if not caixas: return jsonify({"erro": "Rosto não encontrado"}), 400
    novos_encodings = face_recognition.face_encodings(rgb, caixas)
    
    with lock:
        lista_encodings.append(novos_encodings[0])
        lista_nomes.append(nome)
        salvar_dados_pickle()
            
    return jsonify({"mensagem": f"Sucesso! {nome} cadastrado."}), 201

@app.route('/usuarios', methods=['GET'])
def listar():
    return jsonify({"total": len(lista_nomes), "nomes": list(set(lista_nomes))})

@app.route('/video_feed')
def video_feed():
    def gerar():
        while True:
            with lock:
                if frame_atual is None: time.sleep(0.1); continue
                flag, enc = cv2.imencode(".jpg", frame_atual)
                if not flag: continue
            yield(b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + bytearray(enc) + b'\r\n')
    return Response(gerar(), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    carregar_dados()
    t = threading.Thread(target=loop_reconhecimento)
    t.daemon = True
    t.start()
    app.run(host='0.0.0.0', port=5000, debug=False)