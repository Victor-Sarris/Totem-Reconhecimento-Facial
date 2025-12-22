Olá, seja bem vindo. Esse é um repositório destinado ao projeto de tcc que consiste na criação de um artefato tecnológico que resulte em um totem de reconhecimento facial automatizado e ambazado com os conceitos de 'Embedding'.

### É recomendado criar e ativar um ambiente de desenvolvimento:

No CMD:

```
venv\Scripts\activate
```

No PowerShell:

```
.\venv\Scripts\Activate.ps1
```

### Para rodar o projeto é necessário usar as seguintes bibliotecas:

```python

- mediapipe==0.10.21

- deepface

- tf-keras

- cv2

- os

- pickle

```

### Instalação de Bibliotecas (Se for fazer o teste no seu PC)

``` python
pip install mediapipe (versão 0.10.21)

pip install deepface

pip install tf-keras
```

### Instalação de Bibliotecas no Labrador

1. Primeiro, é importante criar e entrar no ambiente de desenvolvimento no Labrador.
2. Em seguida, instale as bibliotecas dentro do Ambiente de Desenvolvimento do Labrador.

Nota: Acesse a documentação para fazer o processo corretamente:
[Ambiente de Desenvolvimento](Documentacao/3.Venv.md)

1. Dependências do Sistema (Terminal Geral)

Antes de tudo, é necessário instalar as bibliotecas matemáticas e gráficas que o OpenCV usa "por baixo do capô". Sem elas, o Python não consegue carregar a biblioteca.

Antes de realizar a instalação de bibliotecas no SO do labrador, certifique de checar as bibliotecas já existentes:

```python
sudo apt update
```

Agora você pode instalar normalmente as bibliotecas que precisa:

```python
sudo apt install -y libopenblas-dev libatlas-base-dev libgtk-3-0 libavcodec-extra
```
```python
sudo apt install ffmpeg -y
```
```python
pip install requests
```

2. Preparação do Ambiente Python

Certifique-se de estar com seu ambiente virtual ativado (se estiver usando um):

```python
source venv/bin/activate
```

Caso o Numpy ou OpenCV já estejam instalados de forma errada (versões incompatíveis ou quebradas), remova-os para começar limpo:

```python
pip uninstall opencv-python numpy -y
```

3. Instalação Otimizada (O "Pulo do Gato")
O segredo para não demorar horas compilando é usar o repositório PiWheels e a flag --prefer-binary.

Instalar o OpenCV (Versão Binary): Isso baixa o arquivo .whl já pronto para ARMv7.

```python
pip install opencv-python --extra-index-url https://www.piwheels.org/simple --prefer-binary
```
(Nota: Isso geralmente instala a versão 4.7.0.72 ou similar compatível)

Instalar o Numpy (Versão Compatível < 2.0): O OpenCV 4.x não funciona com o Numpy 2.0+. Precisamos forçar uma versão anterior (série 1.x) que também seja binária.

```python
pip install "numpy<2" --extra-index-url https://www.piwheels.org/simple --prefer-binary
```

4. Validação

Para confirmar que tudo deu certo, rode o comando abaixo. Se aparecer a versão (ex: 4.7.0) e nenhum erro, o ambiente está pronto.

```python
python3 -c "import cv2; print(f'OpenCV Version: {cv2.__version__}')"
```

Resumo dos Erros Comuns (Troubleshooting)
- Erro libGL.so, libopenblas.so ou libcblas.so: Significa que faltou rodar o passo 1 (dependências do sistema via apt).
- Demora de horas na instalação: Significa que você esqueceu as flags --extra-index-url ... ou --prefer-binary, e o Labrador está tentando compilar o código fonte.
- Erro numpy.core.multiarray failed to import: Significa que você instalou o Numpy 2.0. Remova-o e instale com "numpy<2".

5. 