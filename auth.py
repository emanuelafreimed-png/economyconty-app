import sqlite3
import hashlib
import os
from datetime import datetime

DB_NAME = "financas_comercial.db"

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
            email TEXT UNIQUE,
            nome TEXT NOT NULL,
            senha_hash TEXT NOT NULL,
            salt TEXT NOT NULL,
            plano TEXT DEFAULT 'Gratuito',
            criado_em TEXT
        )
    ''')
    
    # Criar um usuário demo padrão caso a tabela esteja vazia
    c.execute("SELECT COUNT(*) FROM usuarios")
    if c.fetchone()[0] == 0:
        senha_hash, salt = _gerar_hash("123456")
        agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        c.execute('''
            INSERT INTO usuarios (usuario, email, nome, senha_hash, salt, plano, criado_em)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', ("demo", "demo@economyconty.com", "Usuário Demonstração", senha_hash, salt, "Premium", agora))
        
    conn.commit()
    conn.close()

def cadastrar_usuario(usuario, nome, email, senha):
    init_auth_db()
    usuario = usuario.strip().lower()
    email = email.strip().lower() if email else None
    nome = nome.strip()
    
    if len(usuario) < 3:
        return False, "O nome de usuário deve ter pelo menos 3 caracteres.", None
    if len(senha) < 6:
        return False, "A senha deve ter pelo menos 6 caracteres.", None
        
    senha_hash, salt = _gerar_hash(senha)
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    try:
        c.execute('''
            INSERT INTO usuarios (usuario, email, nome, senha_hash, salt, plano, criado_em)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (usuario, email, nome, senha_hash, salt, "Gratuito", agora))
        user_id = c.lastrowid
        conn.commit()
        return True, "Cadastro realizado com sucesso! Faça login para continuar.", user_id
    except sqlite3.IntegrityError as e:
        erro_str = str(e).lower()
        if "email" in erro_str:
            return False, "Este e-mail já está cadastrado.", None
        return False, "Este nome de usuário já está em uso.", None
    finally:
        conn.close()

def verificar_credenciais(identificador, senha):
    init_auth_db()
    identificador = identificador.strip().lower()
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
        SELECT id, usuario, nome, senha_hash, salt, plano 
        FROM usuarios 
        WHERE usuario = ? OR email = ?
    ''', (identificador, identificador))
    row = c.fetchone()
    conn.close()
    
    if not row:
        return False, None, None, None
        
    user_id, usuario, nome, senha_hash_salva, salt, plano = row
    senha_hash_calc, _ = _gerar_hash(senha, salt)
    
    if senha_hash_calc == senha_hash_salva:
        return True, user_id, nome, plano
    return False, None, None, None

def alterar_senha(user_id, senha_atual, nova_senha):
    init_auth_db()
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT senha_hash, salt FROM usuarios WHERE id = ?", (user_id,))
    row = c.fetchone()
    
    if not row:
        conn.close()
        return False, "Usuário não encontrado."
        
    senha_hash_salva, salt = row
    senha_hash_calc, _ = _gerar_hash(senha_atual, salt)
    
    if senha_hash_calc != senha_hash_salva:
        conn.close()
        return False, "Senha atual incorreta."
        
    if len(nova_senha) < 6:
        conn.close()
        return False, "A nova senha deve ter no mínimo 6 caracteres."
        
    novo_hash, novo_salt = _gerar_hash(nova_senha)
    c.execute("UPDATE usuarios SET senha_hash = ?, salt = ? WHERE id = ?", (novo_hash, novo_salt, user_id))
    conn.commit()
    conn.close()
    return True, "Senha alterada com sucesso!"
