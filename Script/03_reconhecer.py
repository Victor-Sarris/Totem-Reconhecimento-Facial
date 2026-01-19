import cv2
import face_recognition
import pickle
import numpy as np
import threading
import time
import requests
from flask import Flask, Response, jsonify, request

# --- CONFIGURAÇÕES ---
ARQUIVO_DADOS = "encodings.pickle"
URL_CAMERA = "http://192.168.18.159/stream" # IP da sua ESP32
DELAY_RECONHECIMENTO = 10  # Tempo (s) de pausa após liberar acesso (Cooldown)
INTERVALO_SCAN_IA = 1.0    # Tempo (s) entre checagens de rosto (Otimização de CPU)

app = Flask(__name__)

# --- VARIÁVEIS GLOBAIS ---
frame_atual = None
lista_encodings = []
lista_nomes = []
lock = threading.Lock()

# --- CARREGAMENTO DE DADOS ---
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
    print("[SISTEMA] Banco de dados salvo.")

# --- THREAD DE VÍDEO E RECONHECIMENTO ---
def loop_reconhecimento():
    global frame_atual, lista_encodings, lista_nomes
    
    ultimo_sucesso = 0        # Para o Cooldown de 10s
    ultimo_check_ia = 0       # Para a Otimização de 1s
    nome_ultimo_detectado = ""
    
    print(f"[VIDEO] Conectando à câmera: {URL_CAMERA}")
    cv2.namedWindow("Totem Facial", cv2.WINDOW_NORMAL)
    # cv2.setWindowProperty("Totem Facial", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
    
    while True:
        try:
            stream = requests.get(URL_CAMERA, stream=True, timeout=5)
            if stream.status_code == 200:
                bytes_buffer = bytes()
                for chunk in stream.iter_content(chunk_size=4096):
                    bytes_buffer += chunk
                    a = bytes_buffer.find(b'\xff\xd8')
                    b = bytes_buffer.find(b'\xff\xd9')
                    
                    if a != -1 and b != -1:
                        jpg = bytes_buffer[a:b+2]
                        bytes_buffer = bytes_buffer[b+2:]
                        
                        # Decodifica frame (Leve)
                        frame = cv2.imdecode(np.frombuffer(jpg, dtype=np.uint8), cv2.IMREAD_COLOR)
                        
                        if frame is not None:
                            agora = time.time()
                            
                            # 1. Verifica se está em Cooldown (Acesso liberado recentemente)
                            tempo_passado_sucesso = agora - ultimo_sucesso
                            em_cooldown = tempo_passado_sucesso < DELAY_RECONHECIMENTO
                            
                            if not em_cooldown:
                                # --- MODO BUSCA ---
                                
                                # OTIMIZAÇÃO: Só roda a IA se passou 1 segundo desde a última vez
                                if (agora - ultimo_check_ia) > INTERVALO_SCAN_IA:
                                    ultimo_check_ia = agora
                                    
                                    # Reduz imagem para IA (Processamento pesado)
                                    small = cv2.resize(frame, (0,0), fx=0.5, fy=0.5)
                                    rgb = cv2.cvtColor(small, cv2.COLOR_BGR2RGB)
                                    
                                    # Detecta rostos
                                    locs = face_recognition.face_locations(rgb)
                                    
                                    if locs and len(lista_encodings) > 0:
                                        encs = face_recognition.face_encodings(rgb, locs)
                                        
                                        for encoding in encs:
                                            with lock: # Leitura segura da lista
                                                matches = face_recognition.compare_faces(lista_encodings, encoding, tolerance=0.5)
                                                name = "Desconhecido"
                                                if True in matches:
                                                    first_match_index = matches.index(True)
                                                    name = lista_nomes[first_match_index]
                                            
                                            if name != "Desconhecido":
                                                print(f"== ACESSO LIBERADO: {name} ==")
                                                ultimo_sucesso = agora
                                                nome_ultimo_detectado = name
                                                
                                                # Feedback imediato no frame atual
                                                cv2.rectangle(frame, (0,0), (frame.shape[1], 60), (0,255,0), -1)
                                                cv2.putText(frame, f"BEM-VINDO {name}", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (255,255,255), 2)
                                                
                                    # Se não achou ninguém, desenha box padrão (opcional)
                                    elif not locs:
                                         cv2.putText(frame, ".", (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 1)

                                else:
                                    # Se NÃO for hora da IA, apenas mostra o vídeo limpo
                                    # Isso economiza muita CPU
                                    pass

                            else:
                                # --- MODO PAUSA (COOLDOWN ATIVO) ---
                                tempo_restante = int(DELAY_RECONHECIMENTO - tempo_passado_sucesso)
                                cv2.rectangle(frame, (0,0), (frame.shape[1], 60), (50,50,50), -1)
                                cv2.putText(frame, f"LIBERADO: {nome_ultimo_detectado}", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,255,0), 2)
                                cv2.putText(frame, f"Proximo em: {tempo_restante}s", (20, frame.shape[0]-20), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,255,255), 2)

                            # MOSTRA O VÍDEO (Sempre fluido)
                            cv2.imshow("Totem Facial", frame)
                            
                            # Atualiza para API
                            with lock:
                                frame_atual = frame.copy()
                            
                            if cv2.waitKey(1) & 0xFF == ord('q'):
                                break
            else:
                time.sleep(1)
        except Exception:
            time.sleep(1)
            
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
            
    print(f"[API] Cadastrado: {nome}")
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