Para rodar local criar venv no python 3.12.9

git clone https://github.com/ErickColombo/trabalho-cloud.git
cd trabalho-cloud
Copie `.env.example` para `.env` e preencha os dados do banco. Não versione o arquivo `.env`.
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python app.py



Para o trabalho: Dentro do servidor EC2

1. Atualizar o Linux e instalar dependências base
sudo apt update && sudo apt upgrade -y
sudo apt install python3-venv python3-pip git libpq-dev -y

2. Clonar o repositório 
git clone https://github.com/ErickColombo/trabalho-cloud.git
cd trabalho-cloud

3. Criar e ativar o ambiente virtual isolado
python3 -m venv venv
source venv/bin/activate

4. Instalar as bibliotecas do projeto (Flask, psycopg2, etc)
pip install -r requirements.txt
