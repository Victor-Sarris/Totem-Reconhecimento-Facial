# 📚🧑‍💻 Documentação - Como utilizar o Putty para conectar via SSH ao Labrador.

### Primeiro passo, instalar o Putty:
![alt text](img-documentation/Putty&Labrador/2.png)
![alt text](img-documentation/Putty&Labrador/3.png)
### Depois de fazer o download e instalação do Putty, vamos inicar o Labrador e descobrir seu IP local para conecta-lo localmente via SSH com sua máquina:
![alt text](img-documentation/Putty&Labrador/4.png)
### Ficou em dúvida se é o IP correto? Não tem problema, podemos testar! Abra o CMD na sua máquina e use o seguinte comando:

```CMD
ping <ip_labrador>
```
### Caso dê tudo certo:
![alt text](img-documentation/Putty&Labrador/5.png)
### Caso dê errado: 
![alt text](img-documentation/Putty&Labrador/erroPing.png)
### Com a etapa anterior bem sucedida, abra o Putty na sua máquina:
![alt text](img-documentation/Putty&Labrador/erroPing.png)
### Configure o Putty corretamente:
![alt text](img-documentation/Putty&Labrador/erroPing.png)
### Entre no Labrador normalmente:
![alt text](img-documentation/Putty&Labrador/8.png)
### 
![alt text](img-documentation/Putty&Labrador/9.png)

<p>Com tudo isso feito, está tudo pronto para avançar para a próxima etapa.<p/>

# Criando um ambiente de desenvolvimento para o seu projeto.
Por quê um ambiente de desenvolvimento é importante?

<p>Um ambiente de desenvolvimento bem configurado é a espinha dorsal de qualquer projeto de software bem-sucedido. Ele serve como uma "oficina" segura e controlada onde você pode construir, testar e quebrar coisas sem causar danos ao produto final ou a outros sistemas.</p>

Aqui está o principal motivo pelo qua ele é indispensável:
```py
1. Isolamento e Gestão de Dependências

Projetos diferentes frequentemente usam versões diferentes das mesmas bibliotecas ou linguagens.

O Problema: Sem isolamento, atualizar uma biblioteca para o "Projeto A" pode quebrar o "Projeto B".

A Solução: Um ambiente de desenvolvimento (usando ferramentas como virtual environments no Python ou containers Docker)
garante que cada projeto tenha suas próprias dependências, sem interferir nos outros ou no sistema operacional principal.

```

### Primeiro de tudo, entre no diretório do projeto:
![alt text](img-documentation/Putty&Labrador/11.png)
### Siga o passo a passo a baixo:
![alt text](img-documentation/Putty&Labrador/12.png)

<p>Pronto, agora você tem um ambiente de desenvolvimento totalmente configurado e pronto para a instalação de bibliotas para o seu projeto!</p>