import cv2
import face_recognition
import pickle
import numpy as np
import threading
import time
import requests
from flask import Flask, Response, jsonify, request

# --- CONFIGURAÇÕES DE REDE ---
ARQUIVO_DADOS = "encodings.pickle"
URL_CAMERA = "http://192.168.18.159/stream" # IP da sua Câmera
DELAY_RECONHECIMENTO = 10
INTERVALO_SCAN_IA = 1.0

# --- OTIMIZAÇÃO DE TELA (HARDCODED FULL HD) ---
# Definimos fixo para poupar CPU de detectar
LARGURA_TELA = 1920
ALTURA_TELA = 1080

app = Flask(__name__)

# --- VARIÁVEIS GLOBAIS ---
frame_atual = None
lista_encodings = []
lista_nomes = []
lock = threading.Lock()

# --- CLASSE DE VÍDEO (BUFFERIZADO + RECONNECT) ---
class VideoStream:
    def __init__(self, src):
        self.src = src
        self.stream = None
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
        while self.rodando:
            try:
                if self.stream is None:
                    self.stream = requests.get(self.src, stream=True, timeout=5)

                for chunk in self.stream.iter_content(chunk_size=4096):
                    if not self.rodando: 
                        if self.stream: self.stream.close()
                        break
                    self.bytes_buffer += chunk
                    a = self.bytes_buffer.find(b'\xff\xd8')
                    b = self.bytes_buffer.find(b'\xff\xd9')
                    if a != -1 and b != -1:
                        jpg = self.bytes_buffer[a:b+2]
                        self.bytes_buffer = self.bytes_buffer[b+2:]
                        with self.lock_video:
                            self.ultimo_frame_jpg = jpg
            except Exception:
                self.stream = None
                self.bytes_buffer = bytes()
                time.sleep(2)

    def read(self):
        with self.lock_video:
            return self.ultimo_frame_jpg

    def stop(self):
        self.rodando = False

# --- FUNÇÕES DE DADOS ---
def carregar_dados():
    global lista_encodings, lista_nomes
    try:
        with open(ARQUIVO_DADOS, "rb") as f:
            data = pickle.load(f)
        lista_encodings = data["encodings"]
        lista_nomes = data["names"]
        print(f"[SISTEMA] Banco carregado: {len(lista_nomes)} usuarios.")
    except FileNotFoundError:
        lista_encodings = []
        lista_nomes = []

def salvar_dados_pickle():
    global lista_encodings, lista_nomes
    with lock:
        data = {"encodings": lista_encodings, "names": lista_nomes}
        with open(ARQUIVO_DADOS, "wb") as f:
            f.write(pickle.dumps(data))

# --- LOOP PRINCIPAL OTIMIZADO ---
def loop_reconhecimento():
    global frame_atual, lista_encodings, lista_nomes
    
    ultimo_sucesso = 0
    ultimo_check_ia = 0
    nome_ultimo_detectado = ""
    janela_configurada = False
    
    print(f"[VIDEO] Iniciando sistema Full HD: {URL_CAMERA}")
    videostream = VideoStream(URL_CAMERA).start()
    time.sleep(2.0)
    
    nome_janela = "Totem Facial"
    cv2.namedWindow(nome_janela, cv2.WINDOW_NORMAL)
    
    while True:
        try:
            jpg_bytes = videostream.read()
            if jpg_bytes is None:
                time.sleep(0.1); continue
                
            frame = cv2.imdecode(np.frombuffer(jpg_bytes, dtype=np.uint8), cv2.IMREAD_COLOR)
            if frame is None: continue

            # 1. ESTICA PARA FULL HD (1920x1080)
            frame = cv2.resize(frame, (LARGURA_TELA, ALTURA_TELA))

            agora = time.time()
            em_cooldown = (agora - ultimo_sucesso) < DELAY_RECONHECIMENTO
            
            if not em_cooldown:
                # OTIMIZAÇÃO MASTER:
                # Só roda IA a cada 1 segundo (INTERVALO_SCAN_IA)
                if (agora - ultimo_check_ia) > INTERVALO_SCAN_IA:
                    ultimo_check_ia = agora
                    
                    # Reduz a imagem 1920x1080 em 80% (fator 0.2) para a IA ler rápido
                    # Isso cria uma imagem interna de 384x216 pixels para o cérebro processar
                    small = cv2.resize(frame, (0,0), fx=0.2, fy=0.2)
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
                                # Desenha na tela grande
                                cv2.rectangle(frame, (0,0), (LARGURA_TELA, 100), (0,255,0), -1)
                                cv2.putText(frame, f"BEM-VINDO {name}", (50, 70), cv2.FONT_HERSHEY_SIMPLEX, 2, (255,255,255), 4)
            else:
                tempo = int(DELAY_RECONHECIMENTO - (agora - ultimo_sucesso))
                cv2.rectangle(frame, (0,0), (LARGURA_TELA, 100), (50,50,50), -1)
                cv2.putText(frame, f"LIBERADO: {nome_ultimo_detectado}", (50, 70), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0,255,0), 3)
                cv2.putText(frame, f"Proximo: {tempo}s", (50, ALTURA_TELA-50), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0,255,255), 3)

            cv2.imshow(nome_janela, frame)
            
            # Configura a janela para Full Screen na primeira execução
            if not janela_configurada:
                cv2.resizeWindow(nome_janela, LARGURA_TELA, ALTURA_TELA)
                cv2.moveWindow(nome_janela, 0, 0)
                cv2.setWindowProperty(nome_janela, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
                janela_configurada = True

            with lock: frame_atual = frame.copy()
            if cv2.waitKey(1) & 0xFF == ord('q'): break
                
        except Exception:
            time.sleep(0.1)
            
    videostream.stop()
    cv2.destroyAllWindows()

# --- API E START ---
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