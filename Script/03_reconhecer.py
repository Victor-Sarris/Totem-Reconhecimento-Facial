import cv2
import face_recognition
import pickle
import numpy as np
import threading
import time
import requests
import subprocess
from flask import Flask, Response, jsonify, request

# --- CONFIGURAÇÕES ---
ARQUIVO_DADOS = "encodings.pickle"
URL_CAMERA = "http://192.168.18.159/stream"
DELAY_RECONHECIMENTO = 10
INTERVALO_SCAN_IA = 1.0

app = Flask(__name__)

# --- VARIÁVEIS GLOBAIS ---
frame_atual = None
lista_encodings = []
lista_nomes = []
lock = threading.Lock()
LARGURA_TELA = 800  # Valor padrao (sera atualizado automaticamente)
ALTURA_TELA = 480   # Valor padrao

# --- DETECTOR DE RESOLUÇÃO AUTOMÁTICO ---
def detectar_resolucao():
    """Pergunta ao Linux qual o tamanho real do monitor"""
    global LARGURA_TELA, ALTURA_TELA
    try:
        # Executa o comando xrandr para pegar a resolução atual com asterisco (*)
        cmd = "xrandr | grep '*' | awk '{print $1}'"
        output = subprocess.check_output(cmd, shell=True).decode().strip()
        
        if output:
            w, h = output.split('x')
            LARGURA_TELA = int(w)
            ALTURA_TELA = int(h)
            print(f"[TELA] Resolução detectada: {LARGURA_TELA}x{ALTURA_TELA}")
        else:
            print("[TELA] Não foi possível detectar. Usando padrão 800x480.")
    except Exception as e:
        print(f"[TELA] Erro ao detectar: {e}. Usando padrão.")

# --- CLASSE DE VÍDEO ---
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
        print("[AVISO] Iniciando banco de dados vazio.")
        lista_encodings = []
        lista_nomes = []

def salvar_dados_pickle():
    global lista_encodings, lista_nomes
    with lock:
        data = {"encodings": lista_encodings, "names": lista_nomes}
        with open(ARQUIVO_DADOS, "wb") as f:
            f.write(pickle.dumps(data))

# --- LOOP PRINCIPAL ---
def loop_reconhecimento():
    global frame_atual, lista_encodings, lista_nomes, LARGURA_TELA, ALTURA_TELA
    
    ultimo_sucesso = 0
    ultimo_check_ia = 0
    nome_ultimo_detectado = ""
    
    # 1. Detecta o tamanho da tela ANTES de começar
    detectar_resolucao()
    
    print(f"[VIDEO] Iniciando buffer de vídeo: {URL_CAMERA}")
    videostream = VideoStream(URL_CAMERA).start()
    time.sleep(2.0)
    
    nome_janela = "Totem Facial"
    cv2.namedWindow(nome_janela, cv2.WINDOW_NORMAL)
    
    # Configura Tela Cheia
    cv2.setWindowProperty(nome_janela, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
    
    # Força tamanho (caso o fullscreen falhe em alguns monitores)
    cv2.resizeWindow(nome_janela, LARGURA_TELA, ALTURA_TELA)
    cv2.moveWindow(nome_janela, 0, 0)
    
    while True:
        try:
            jpg_bytes = videostream.read()
            if jpg_bytes is None:
                time.sleep(0.1); continue
                
            frame = cv2.imdecode(np.frombuffer(jpg_bytes, dtype=np.uint8), cv2.IMREAD_COLOR)
            if frame is None: continue

            # 2. ESTICA A IMAGEM PARA O TAMANHO DETECTADO
            frame = cv2.resize(frame, (LARGURA_TELA, ALTURA_TELA))

            agora = time.time()
            em_cooldown = (agora - ultimo_sucesso) < DELAY_RECONHECIMENTO
            
            if not em_cooldown:
                # OTIMIZAÇÃO IA (Usa imagem pequena para processar rápido)
                if (agora - ultimo_check_ia) > INTERVALO_SCAN_IA:
                    ultimo_check_ia = agora
                    # Reduz a imagem só para o cérebro (IA) ler rápido
                    # Usamos proporção fixa para não distorcer o rosto na leitura
                    small = cv2.resize(frame, (0,0), fx=0.25, fy=0.25)
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
                                cv2.rectangle(frame, (0,0), (LARGURA_TELA, 80), (0,255,0), -1)
                                cv2.putText(frame, f"BEM-VINDO {name}", (40, 60), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (255,255,255), 3)
            else:
                tempo = int(DELAY_RECONHECIMENTO - (agora - ultimo_sucesso))
                cv2.rectangle(frame, (0,0), (LARGURA_TELA, 80), (50,50,50), -1)
                cv2.putText(frame, f"LIBERADO: {nome_ultimo_detectado}", (40, 60), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0,255,0), 3)
                cv2.putText(frame, f"Proximo: {tempo}s", (40, ALTURA_TELA-40), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0,255,255), 2)

            cv2.imshow(nome_janela, frame)
            with lock: frame_atual = frame.copy()
            
            if cv2.waitKey(1) & 0xFF == ord('q'): break
                
        except Exception:
            time.sleep(0.1)
            
    videostream.stop()
    cv2.destroyAllWindows()

# --- API FLASK ---
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