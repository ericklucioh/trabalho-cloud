import os
import psycopg2
from psycopg2.extras import RealDictCursor
from flask import Flask, render_template, request, redirect, url_for
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

def get_db_connection():
    return psycopg2.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        database=os.getenv('DB_NAME', 'trabalho-cloud'),
        user=os.getenv('DB_USER', 'postgres'),
        password=os.getenv('DB_PASS'),
        port=os.getenv('DB_PORT', '5432')
    )

# Cria a tabela de exemplo ao iniciar
with get_db_connection() as conn:
    with conn.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS usuarios (
                id SERIAL PRIMARY KEY,
                nome VARCHAR(100) NOT NULL,
                email VARCHAR(100) UNIQUE NOT NULL
            )
        """)
    conn.commit()

# READ: Carrega a página com a lista
@app.route('/')
def index():
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT * FROM usuarios ORDER BY id")
    usuarios = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('index.html', usuarios=usuarios)

# CREATE: Recebe dados do formulário e salva
@app.route('/adicionar', methods=['POST'])
def adicionar():
    nome = request.form['nome']
    email = request.form['email']
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO usuarios (nome, email) VALUES (%s, %s)", (nome, email))
    conn.commit()
    cur.close()
    conn.close()
    return redirect(url_for('index'))

# UPDATE: Recebe dados do formulário flutuante e atualiza
@app.route('/atualizar/<int:id>', methods=['POST'])
def atualizar(id):
    nome = request.form['nome']
    email = request.form['email']
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("UPDATE usuarios SET nome = %s, email = %s WHERE id = %s", (nome, email, id))
    conn.commit()
    cur.close()
    conn.close()
    return redirect(url_for('index'))

# DELETE: Deleta e recarrega a página
@app.route('/deletar/<int:id>', methods=['POST'])
def deletar(id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM usuarios WHERE id = %s", (id,))
    conn.commit()
    cur.close()
    conn.close()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(
        host=os.getenv('FLASK_HOST', '0.0.0.0'),
        debug=os.getenv('FLASK_DEBUG', 'false').strip().lower() == 'true',
        port=5000
    )
