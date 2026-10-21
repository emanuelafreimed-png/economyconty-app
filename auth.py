import sqlite3
import hashlib
import os
from datetime import datetime

DB_NAME = "financas.db"

def _gerar_hash(senha, salt=None):
    if salt is None:
        salt = os.urandom(16).hex()
    hash_obj = hashlib.sha256((senha + salt).encode('utf-8'))
    return hash_obj.hexdigest(), salt

def init_auth_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario TEXT UNIQUE NOT NULL,
            nome TEXT NOT NULL,
            senha_hash TEXT NOT NULL,
            salt TEXT NOT NULL,
            criado_em TEXT
        )
    ''')
    
    # Se não houver nenhum usuário, cria o usuário master da Emanuela Freires
    c.execute("SELECT COUNT(*) FROM usuarios")
    if c.fetchone()[0] == 0:
        senha_hash, salt = _gerar_hash("conty2026")
        agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        c.execute('''
            INSERT INTO usuarios (usuario, nome, senha_hash, salt, criado_em)
            VALUES (?, ?, ?, ?, ?)
        ''', ("emanuela", "Emanuela Freires", senha_hash, salt, agora))
        
    conn.commit()
    conn.close()

def cadastrar_usuario(usuario, nome, senha):
    init_auth_db()
    senha_hash, salt = _gerar_hash(senha)
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    sucesso = False
    try:
        c.execute('''
            INSERT INTO usuarios (usuario, nome, senha_hash, salt, criado_em)
            VALUES (?, ?, ?, ?, ?)
        ''', (usuario.strip().lower(), nome.strip(), senha_hash, salt, agora))
        conn.commit()
        sucesso = True
    except sqlite3.IntegrityError:
        sucesso = False
    finally:
        conn.close()
    return sucesso

def verificar_credenciais(usuario, senha):
    init_auth_db()
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT nome, senha_hash, salt FROM usuarios WHERE usuario = ?", (usuario.strip().lower(),))
    row = c.fetchone()
    conn.close()
    
    if not row:
        return False, None
        
    nome, senha_hash_salva, salt = row
    senha_hash_calc, _ = _gerar_hash(senha, salt)
    
    if senha_hash_calc == senha_hash_salva:
        return True, nome
    return False, None

def alterar_senha(usuario, senha_atual, nova_senha):
    init_auth_db()
    autenticado, nome = verificar_credenciais(usuario, senha_atual)
    if not autenticado:
        return False, "Senha atual incorreta."
        
    if len(nova_senha) < 6:
        return False, "A nova senha deve ter no mínimo 6 caracteres."
        
    senha_hash, salt = _gerar_hash(nova_senha)
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("UPDATE usuarios SET senha_hash = ?, salt = ? WHERE usuario = ?", (senha_hash, salt, usuario.strip().lower()))
    conn.commit()
    conn.close()
    return True, "Senha alterada com sucesso!"
