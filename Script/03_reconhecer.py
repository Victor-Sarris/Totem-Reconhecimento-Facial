import cv2
import face_recognition
import pickle
import numpy as np
import threading
import time
import requests
from flask import Flask, Response, jsonify, request

# config
ARQUIVO_DADOS = "encodings.pickle"
URL_CAMERA = "http://192.168.18.159/stream" # IP espcam
DELAY_RECONHECIMENTO = 10  # tempo em segundos que o sistema pausa após reconhecer alguém

app = Flask(__name__)

# variaveis globais
frame_atual = None
lista_encodings = []
lista_nomes = []
lock = threading.Lock() # evita que o cadastro atrapalhe o reconhecimento

#  carregamento de dados 
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
    # usa o threading.Lock para garantir que ninguém mexa na lista enquanto salvamos
    with lock:
        data = {"encodings": lista_encodings, "names": lista_nomes}
        with open(ARQUIVO_DADOS, "wb") as f:
            f.write(pickle.dumps(data))
    print("[SISTEMA] Banco de dados atualizado e salvo.")

# inicia o reconhecimento 
def loop_reconhecimento():
    global frame_atual, lista_encodings, lista_nomes
    
    ultimo_reconhecimento = 0
    nome_ultimo_detectado = ""
    
    print(f"[VIDEO] Iniciando janela e conectando: {URL_CAMERA}")
    
    # cria a janela no monitor externo
    cv2.namedWindow("Totem Facial", cv2.WINDOW_NORMAL)
    # cv2.setWindowProperty("Totem Facial", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN) # Descomente se quiser tela cheia
    
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
                        
                        # decodifica o frame
                        frame = cv2.imdecode(np.frombuffer(jpg, dtype=np.uint8), cv2.IMREAD_COLOR)
                        
                        if frame is not None:
                            # delay de 10 segundos entre um reconhecimento e outro
                            # pensei nisso para diminuir o processamento da cpu do labrador
                            agora = time.time()
                            tempo_passado = agora - ultimo_reconhecimento
                            em_cooldown = tempo_passado < DELAY_RECONHECIMENTO
                            
                            if not em_cooldown:
                                # inicia o reconhecimento
                                small = cv2.resize(frame, (0,0), fx=0.5, fy=0.5)
                                rgb = cv2.cvtColor(small, cv2.COLOR_BGR2RGB)
                                
                                # detecta rostos
                                locs = face_recognition.face_locations(rgb)
                                
                                # só tenta reconhecer se tiver rostos E se tiver gente cadastrada
                                if locs and len(lista_encodings) > 0:
                                    encs = face_recognition.face_encodings(rgb, locs)
                                    
                                    for encoding in encs:
                                        # usa o lock para ler a lista com segurança
                                        with lock:
                                            matches = face_recognition.compare_faces(lista_encodings, encoding, tolerance=0.5)
                                            name = "Desconhecido"
                                            if True in matches:
                                                first_match_index = matches.index(True)
                                                name = lista_nomes[first_match_index]
                                        
                                        if name != "Desconhecido":
                                            print(f"== ACESSO LIBERADO: {name} ==")
                                            ultimo_reconhecimento = agora
                                            nome_ultimo_detectado = name
                                            
                                            # visual indicativo verde "acesso liberado" no topo da tela
                                            cv2.rectangle(frame, (0,0), (frame.shape[1], 60), (0,255,0), -1)
                                            cv2.putText(frame, f"BEM-VINDO {name}", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (255,255,255), 2)
                                else:
                                    # Ninguém na frente ou banco vazio
                                    cv2.rectangle(frame, (0, 0), (frame.shape[1], 30), (0, 0, 255), -1)
                                    cv2.putText(frame, "APROXIME O ROSTO", (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)

                            else:
                                # --- MODO PAUSA (COOLDOWN) ---
                                tempo_restante = int(DELAY_RECONHECIMENTO - tempo_passado)
                                cv2.rectangle(frame, (0,0), (frame.shape[1], 60), (50,50,50), -1)
                                cv2.putText(frame, f"LIBERADO: {nome_ultimo_detectado}", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,255,0), 2)
                                cv2.putText(frame, f"Proximo em: {tempo_restante}s", (20, frame.shape[0]-20), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,255,255), 2)

                            # mostra a janela na tela hdmi
                            cv2.imshow("Totem Facial", frame)
                            
                            # atualiza o frame para a api ()
                            with lock:
                                frame_atual = frame.copy()
                            
                            if cv2.waitKey(1) & 0xFF == ord('q'):
                                break
            else:
                time.sleep(1) 
        except Exception as e:
            # print(f"Erro câmera: {e}") 
            time.sleep(1)

    cv2.destroyAllWindows()

# --- API FLASK (ROTA NOVA PARA CADASTRAR SEM PARAR O TOTEM) ---

@app.route('/api/cadastrar_direto', methods=['POST'])
def cadastrar_direto():
    global lista_encodings, lista_nomes
    
    if 'foto' not in request.files or 'nome' not in request.form:
        return jsonify({"erro": "Faltou foto ou nome"}), 400
    
    arquivo = request.files['foto']
    nome = request.form['nome']
    
    # processa a imagem na memória RAM
    npimg = np.frombuffer(arquivo.read(), np.uint8)
    img = cv2.imdecode(npimg, cv2.IMREAD_COLOR)
    rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    
    # eera embedding
    caixas = face_recognition.face_locations(rgb)
    if not caixas:
        return jsonify({"erro": "Rosto não encontrado na foto enviada"}), 400
        
    novos_encodings = face_recognition.face_encodings(rgb, caixas)
    
    # adiciona na lista PRINCIPAL (protegido pelo lock)
    with lock:
        lista_encodings.append(novos_encodings[0])
        lista_nomes.append(nome)
        
        # salva no disco
        data = {"encodings": lista_encodings, "names": lista_nomes}
        with open(ARQUIVO_DADOS, "wb") as f:
            f.write(pickle.dumps(data))
            
    print(f"[API] Novo usuário cadastrado: {nome}")
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

# --- INICIALIZAÇÃO ---
if __name__ == '__main__':
    carregar_dados()
    
    # Inicia o Totem (Janela + Reconhecimento) em paralelo
    t = threading.Thread(target=loop_reconhecimento)
    t.daemon = True
    t.start()
    
    # Inicia a API para receber cadastros
    app.run(host='0.0.0.0', port=5000, debug=False)