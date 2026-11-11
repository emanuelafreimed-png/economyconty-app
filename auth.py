import sqlite3
import hashlib
import os
from datetime import datetime

DB_NAME = "financas_comercial.db"

TERMO_ACEITE_LGPD_TEXTO = """
#### 📜 TERMO DE ACEITE, PRIVACIDADE DE DADOS (LGPD) E REGRAS DE USO — PROGRAMA DE TESTES (BETA)
**Aplicativo:** EconomyContY • Inteligência Financeira & Patrimonial

Ao criar sua conta ou acessar o ambiente de testes do **EconomyContY**, você declara ter lido e concordado com as diretrizes abaixo:

**1. Finalidade do Ambiente de Testes (Versão Beta)**
* **1.1.** O aplicativo encontra-se em fase de **avaliação e homologação (Beta Test)**, tendo como objetivo validar funcionalidades de organização financeira pessoal, Regra 50/30/20, leitura inteligente de cupons/extratos, gestão de patrimônio e planejamento de metas (*Sonhos & Caixinhas*).
* **1.2. Isenção de Consultoria Regulatória:** Os indicadores, projeções de CDI/Selic e análises geradas pela assistente virtual **Manu** possuem caráter exclusivamente **educativo, informativo e organizacional**, não configurando recomendação oficial de compra/venda de ativos (CVM) ou declaração oficial de Imposto de Renda junto à Receita Federal.

**2. Segurança e Privacidade dos Seus Dados (Conformidade LGPD — Lei nº 13.709/2018)**
* **2.1. Criptografia de Credenciais:** Sua senha de acesso é protegida por criptografia unidirecional **SHA-256 combinada com Salt aleatório de 128 bits**. Nem mesmo os administradores do sistema têm acesso à sua senha em texto aberto.
* **2.2. Isolamento de Conta (Multi-Tenant):** Todos os lançamentos, metas, patrimônio, caixinhas e faturas cadastrados são vinculados exclusivamente ao seu identificador único (`user_id`), sendo invisíveis para outros usuários do sistema.
* **2.3. Ausência de Vínculo Bancário Direto:** O EconomyContY **NÃO solicita e NÃO armazena** senhas bancárias, tokens, número completo de cartão de crédito, CVV ou CPF, e não realiza movimentações financeiras reais.
* **2.4. Processamento Volátil de Documentos e Imagens:** Fotos de cupons fiscais, recibos, PDFs e planilhas CSV/Excel enviados para importação são processados **apenas em memória temporária (RAM)** para extração dos textos e valores, **não ficando armazenados como arquivos de imagem/documento** no servidor.
* **2.5. Autonomia e Exclusão (Art. 18 da LGPD):** Você possui controle total sobre seus registros, podendo editar, exportar ou excluir definitivamente seus lançamentos, faturas, metas e dados patrimoniais a qualquer momento dentro do próprio aplicativo.

**3. Recomendações e Regras para o Testador**
* **3.1.** Durante o período de testes em nuvem, recomendamos que o usuário **mantenha cópia/backup próprio** de suas planilhas originais, pois atualizações técnicas da versão Beta podem ocorrer.
* **3.2.** Nunca insira senhas bancárias ou códigos de segurança nos campos de descrição.
* **3.3.** O usuário compromete-se a reportar eventuais falhas (*bugs*) ou sugestões de melhoria à equipe responsável pelo projeto e a não compartilhar indevidamente credenciais de acesso.
"""

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
            criado_em TEXT,
            aceite_termos_em TEXT
        )
    ''')
    c.execute("PRAGMA table_info(usuarios)")
    cols_usr = [col[1] for col in c.fetchall()]
    if "aceite_termos_em" not in cols_usr:
        c.execute("ALTER TABLE usuarios ADD COLUMN aceite_termos_em TEXT")
    
    # Criar um usuário demo padrão caso a tabela esteja vazia
    c.execute("SELECT COUNT(*) FROM usuarios")
    if c.fetchone()[0] == 0:
        senha_hash, salt = _gerar_hash("123456")
        agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        c.execute('''
            INSERT INTO usuarios (usuario, email, nome, senha_hash, salt, plano, criado_em, aceite_termos_em)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', ("demo", "demo@economyconty.com", "Usuário Demonstração", senha_hash, salt, "Premium", agora, agora))
        
    conn.commit()
    conn.close()

def cadastrar_usuario(usuario, nome, email, senha, aceitou_termos=True):
    init_auth_db()
    usuario = usuario.strip().lower()
    email = email.strip().lower() if email else None
    nome = nome.strip()
    
    if not aceitou_termos:
        return False, "É obrigatório ler e aceitar o Termo de Uso e Privacidade de Dados (LGPD) para criar sua conta.", None
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
            INSERT INTO usuarios (usuario, email, nome, senha_hash, salt, plano, criado_em, aceite_termos_em)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (usuario, email, nome, senha_hash, salt, "Gratuito", agora, agora))
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
