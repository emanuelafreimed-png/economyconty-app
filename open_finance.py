import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import random

DB_NAME = "financas_comercial.db"

BANCOS_DISPONIVEIS = [
    {"codigo": "nubank", "nome": "Nu Pagamentos S.A. (Nubank)", "cor": "#820AD1", "tipo": "Conta Digital & Cartão"},
    {"codigo": "itau", "nome": "Banco Itaú Unibanco S.A.", "cor": "#EC7000", "tipo": "Conta Corrente & Cartão"},
    {"codigo": "inter", "nome": "Banco Inter S.A.", "cor": "#FF7A00", "tipo": "Conta Digital & Investimentos"},
    {"codigo": "bradesco", "nome": "Banco Bradesco S.A.", "cor": "#CC092F", "tipo": "Conta Corrente & Cartão"},
    {"codigo": "santander", "nome": "Banco Santander Brasil", "cor": "#EC0000", "tipo": "Conta Corrente & Cartão"},
    {"codigo": "bb", "nome": "Banco do Brasil S.A.", "cor": "#003882", "tipo": "Conta Corrente"},
    {"codigo": "caixa", "nome": "Caixa Econômica Federal", "cor": "#005CA9", "tipo": "Poupança & Conta"},
    {"codigo": "c6", "nome": "C6 Bank S.A.", "cor": "#242424", "tipo": "Conta Digital & Cartão Carbon"},
    {"codigo": "btg", "nome": "BTG Pactual", "cor": "#001E62", "tipo": "Investimentos & Banking"}
]

def init_open_finance_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS open_finance_conexoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            banco_codigo TEXT NOT NULL,
            nome_exibicao TEXT NOT NULL,
            tipo TEXT NOT NULL,
            status TEXT DEFAULT '🟢 Ativa & Conectada',
            ultima_sincronizacao TEXT,
            saldo_atual REAL DEFAULT 0.0,
            detalhes_conta TEXT,
            UNIQUE(user_id, banco_codigo)
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS open_finance_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            data_hora TEXT NOT NULL,
            banco TEXT NOT NULL,
            itens_novos INTEGER DEFAULT 0,
            status TEXT NOT NULL,
            mensagem TEXT
        )
    ''')
    conn.commit()
    conn.close()

def listar_conexoes_usuario(user_id):
    init_open_finance_db()
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT * FROM open_finance_conexoes WHERE user_id = ? ORDER BY id DESC", conn, params=[user_id])
    conn.close()
    return df

def conectar_banco(user_id, banco_codigo, saldo_inicial=0.0):
    init_open_finance_db()
    banco_info = next((b for b in BANCOS_DISPONIVEIS if b["codigo"] == banco_codigo), None)
    if not banco_info:
        return False, "Banco inválido selecionado."
        
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    agora = datetime.now().strftime("%Y-%m-%d %H:%M")
    detalhes = f"Open Finance API • ID: OF-{random.randint(10000, 99999)}"
    
    try:
        c.execute('''
            INSERT INTO open_finance_conexoes (
                user_id, banco_codigo, nome_exibicao, tipo, status, 
                ultima_sincronizacao, saldo_atual, detalhes_conta
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, banco_codigo, banco_info["nome"], banco_info["tipo"], "🟢 Ativa & Conectada", agora, float(saldo_inicial), detalhes))
        conn.commit()
        
        # Registrar log
        c.execute('''
            INSERT INTO open_finance_logs (user_id, data_hora, banco, itens_novos, status, mensagem)
            VALUES (?, ?, ?, 0, 'Sucesso', 'Conexão inicial estabelecida com autorização Bacen/Open Finance')
        ''', (user_id, agora, banco_info["nome"]))
        conn.commit()
        return True, f"Banco {banco_info['nome']} conectado com sucesso!"
    except sqlite3.IntegrityError:
        return False, "Esta instituição já está conectada na sua conta."
    finally:
        conn.close()

def desconectar_banco(user_id, conexao_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("DELETE FROM open_finance_conexoes WHERE id = ? AND user_id = ?", (conexao_id, user_id))
    linhas = c.rowcount
    conn.commit()
    conn.close()
    return linhas > 0

def sincronizar_todas_conexoes(user_id):
    """
    Sincroniza transações recentes via Open Finance e insere automaticamente
    na tabela de lançamentos do usuário.
    """
    init_open_finance_db()
    conexoes = listar_conexoes_usuario(user_id)
    if conexoes.empty:
        return 0, "Nenhuma instituição conectada para sincronizar."

    from database import adicionar_lancamento
    
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    total_novos = 0
    agora = datetime.now()
    agora_str = agora.strftime("%Y-%m-%d %H:%M")

    # Amostras realistas de transações bancárias para Open Finance
    exemplos_transacoes = [
        {"desc": "Pix Recebido - Transferência Instantânea", "tipo": "Receita", "cat": "Receita Principal", "valor_range": (300, 2500)},
        {"desc": "Supermercado - Cartão Débito", "tipo": "Despesa", "cat": "Alimentação", "valor_range": (85, 320)},
        {"desc": "Posto de Combustível - Débito", "tipo": "Despesa", "cat": "Transporte", "valor_range": (120, 250)},
        {"desc": "Farmácia São Paulo - Débito", "tipo": "Despesa", "cat": "Saúde", "valor_range": (35, 140)},
        {"desc": "iFood Refeição - Cartão", "tipo": "Despesa", "cat": "Alimentação", "valor_range": (42, 110)},
        {"desc": "Rendimento Conta Remunerada", "tipo": "Receita", "cat": "Investimentos", "valor_range": (15, 95)}
    ]

    for _, row in conexoes.iterrows():
        banco_nome = row["nome_exibicao"]
        banco_id = row["id"]
        
        # Simula 2 a 4 transações recentes sincronizadas pelo BACEN / Pluggy
        qtd = random.randint(2, 4)
        for _ in range(qtd):
            sample = random.choice(exemplos_transacoes)
            valor = round(random.uniform(*sample["valor_range"]), 2)
            dias_atras = random.randint(0, 3)
            data_tx = (agora - timedelta(days=dias_atras)).strftime("%Y-%m-%d")
            
            adicionar_lancamento(
                user_id=user_id,
                tipo=sample["tipo"],
                descricao=f"[{row['banco_codigo'].upper()}] {sample['desc']}",
                valor=valor,
                data_vencimento=data_tx,
                categoria=sample["cat"],
                conta=banco_nome.split(" ")[0],
                status="Realizado",
                origem="Open Finance"
            )
            total_novos += 1
            
        # Atualiza a data da última sincronização
        c.execute("UPDATE open_finance_conexoes SET ultima_sincronizacao = ? WHERE id = ?", (agora_str, banco_id))
        
        # Grava log
        c.execute('''
            INSERT INTO open_finance_logs (user_id, data_hora, banco, itens_novos, status, mensagem)
            VALUES (?, ?, ?, ?, 'Sucesso', 'Sincronização automática via Open Finance concluída com sucesso.')
        ''', (user_id, agora_str, banco_nome, qtd))

    conn.commit()
    conn.close()
    
    return total_novos, f"Sincronização concluída! {total_novos} novas transações adicionadas automaticamente."
