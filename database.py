import os
import sqlite3
import pandas as pd
from datetime import datetime

DB_NAME = os.path.join(os.path.dirname(os.path.abspath(__file__)), "financas.db")

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    # Tabela de lançamentos (Receitas e Despesas)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS lancamentos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tipo TEXT,
            descricao TEXT,
            valor REAL,
            data_vencimento TEXT,
            categoria_503020 TEXT,
            banco TEXT,
            status TEXT,
            protocolo TEXT,
            data_pagamento TEXT,
            tributavel INTEGER DEFAULT 0,
            dedutivel INTEGER DEFAULT 0
        )
    ''')
    
    # Try adding protocolo column if it doesn't exist
    try:
        cursor.execute("ALTER TABLE lancamentos ADD COLUMN protocolo TEXT")
    except sqlite3.OperationalError:
        pass
        
    try:
        cursor.execute("ALTER TABLE lancamentos ADD COLUMN data_pagamento TEXT")
    except sqlite3.OperationalError:
        pass
        
    try:
        cursor.execute("ALTER TABLE lancamentos ADD COLUMN tributavel INTEGER DEFAULT 0")
    except sqlite3.OperationalError:
        pass
        
    # Tabela de Patrimônio/Investimentos
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS patrimonio (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ativo TEXT UNIQUE,
            saldo REAL,
            data_atualizacao TEXT
        )
    ''')
    
    # Tabela de Histórico de Patrimônio (Evolução no Tempo)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS historico_patrimonio (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data_registro TEXT,
            total REAL
        )
    ''')
    
    # Tabela de Saldo Inicial de Conta Bancária por Ano
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS saldo_inicial (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            banco TEXT,
            ano INTEGER,
            valor REAL,
            UNIQUE(banco, ano)
        )
    ''')
    
    # Inserir os ativos padrão se a tabela estiver vazia
    cursor.execute('SELECT COUNT(*) FROM patrimonio')
    if cursor.fetchone()[0] == 0:
        ativos_padrao = [
            "CDB Itaú", "Previdência Privada", "Fundos de Investimento",
            "Cofrinho Itaú", "FGTS", "Binance", 
            "Saldo Bancário CAIXA", "Saldo Bancário Itaú", "Saldo Bancário NU BANK"
        ]
        for ativo in ativos_padrao:
            cursor.execute('INSERT INTO patrimonio (ativo, saldo, data_atualizacao) VALUES (?, 0.0, date("now"))', (ativo,))
            
    conn.commit()
    conn.close()

from datetime import date

def registrar_historico_patrimonio(total, data_registro=None):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Normalizar rigorosamente para o 1º dia do mês (AAAA-MM-01)
    if data_registro is None:
        hoje = datetime.now()
        data_mes = f"{hoje.year:04d}-{hoje.month:02d}-01"
    elif isinstance(data_registro, (date, datetime)):
        data_mes = f"{data_registro.year:04d}-{data_registro.month:02d}-01"
    else:
        try:
            dt = pd.to_datetime(data_registro)
            data_mes = f"{dt.year:04d}-{dt.month:02d}-01"
        except Exception:
            hoje = datetime.now()
            data_mes = f"{hoje.year:04d}-{hoje.month:02d}-01"

    mes_ano = data_mes[:7] # 'AAAA-MM'
    cursor.execute("SELECT id FROM historico_patrimonio WHERE data_registro LIKE ? OR data_registro = ?", (f"{mes_ano}%", data_mes))
    rows = cursor.fetchall()
    if rows:
        primeiro_id = rows[0][0]
        cursor.execute("UPDATE historico_patrimonio SET data_registro = ?, total = ? WHERE id = ?", (data_mes, float(total), primeiro_id))
        if len(rows) > 1:
            outros_ids = [r[0] for r in rows[1:]]
            cursor.execute(f"DELETE FROM historico_patrimonio WHERE id IN ({','.join(['?']*len(outros_ids))})", outros_ids)
    else:
        cursor.execute("INSERT INTO historico_patrimonio (data_registro, total) VALUES (?, ?)", (data_mes, float(total)))
        
    conn.commit()
    conn.close()

def listar_historico_patrimonio():
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT * FROM historico_patrimonio ORDER BY data_registro ASC", conn)
    conn.close()
    if not df.empty:
        # Garante que cada mês tem exatamente um registro consolidado (AAAA-MM-01)
        df['competencia_mes'] = pd.to_datetime(df['data_registro']).dt.strftime('%Y-%m-01')
        df = df.groupby('competencia_mes', as_index=False).agg({'id': 'last', 'total': 'last'})
        df['data_registro'] = df['competencia_mes']
        df = df.sort_values('data_registro').reset_index(drop=True)
    return df

def excluir_historico_patrimonio(id_hist):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM historico_patrimonio WHERE id = ?", (id_hist,))
    conn.commit()
    conn.close()

def inserir_lancamento(tipo, descricao, valor, data_vencimento, categoria_503020, banco, status, protocolo=None, data_pagamento=None, tributavel=0, dedutivel=0):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO lancamentos (tipo, descricao, valor, data_vencimento, categoria_503020, banco, status, protocolo, data_pagamento, tributavel, dedutivel)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (tipo, descricao, valor, data_vencimento, categoria_503020, banco, status, protocolo, data_pagamento, tributavel, dedutivel))
    conn.commit()
    conn.close()

def listar_lancamentos():
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT * FROM lancamentos", conn)
    conn.close()
    return df

def listar_patrimonio():
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT * FROM patrimonio ORDER BY id ASC", conn)
    conn.close()
    return df

def atualizar_patrimonio(ativo, novo_saldo, data_atualizacao):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE patrimonio 
        SET saldo = ?, data_atualizacao = ?
        WHERE ativo = ?
    ''', (novo_saldo, data_atualizacao, ativo))
    conn.commit()
    conn.close()

def adicionar_ativo(nome_ativo):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute('INSERT INTO patrimonio (ativo, saldo, data_atualizacao) VALUES (?, 0.0, date("now"))', (nome_ativo,))
        conn.commit()
    except sqlite3.IntegrityError:
        pass
    conn.close()

def excluir_ativo(nome_ativo):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM patrimonio WHERE ativo = ?', (nome_ativo,))
    conn.commit()
    conn.close()

def excluir_lancamento(id_lancamento):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM lancamentos WHERE id = ?', (id_lancamento,))
    conn.commit()
    conn.close()

def excluir_lancamento_protocolo(protocolo):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM lancamentos WHERE protocolo = ?', (protocolo,))
    conn.commit()
    conn.close()

def excluir_lancamentos_multiplos(lista_ids):
    if not lista_ids:
        return
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    placeholders = ','.join(['?'] * len(lista_ids))
    cursor.execute(f"DELETE FROM lancamentos WHERE id IN ({placeholders})", tuple(lista_ids))
    conn.commit()
    conn.close()

def atualizar_categoria_lancamento(id_lancamento, nova_categoria):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('UPDATE lancamentos SET categoria_503020 = ? WHERE id = ?', (nova_categoria, id_lancamento))
    conn.commit()
    conn.close()

def atualizar_categorias_lote(lista_alteracoes):
    """lista_alteracoes: lista de tuplas (nova_categoria, id_lancamento)"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.executemany('UPDATE lancamentos SET categoria_503020 = ? WHERE id = ?', lista_alteracoes)
    conn.commit()
    conn.close()

def obter_saldo_inicial(banco="Itaú", ano=2026):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT valor FROM saldo_inicial WHERE banco = ? AND ano = ?", (banco, ano))
    row = cursor.fetchone()
    conn.close()
    return float(row[0]) if row and row[0] is not None else 0.0

def salvar_saldo_inicial(banco, ano, valor):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM saldo_inicial WHERE banco = ? AND ano = ?", (banco, ano))
    row = cursor.fetchone()
    if row:
        cursor.execute("UPDATE saldo_inicial SET valor = ? WHERE id = ?", (float(valor), row[0]))
    else:
        cursor.execute("INSERT INTO saldo_inicial (banco, ano, valor) VALUES (?, ?, ?)", (banco, ano, float(valor)))
    conn.commit()
    conn.close()

init_db()

