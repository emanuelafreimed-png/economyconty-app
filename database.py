import os
import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime, date
import io
import re

DB_NAME = os.path.join(os.path.dirname(os.path.abspath(__file__)), "financas_comercial.db")

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Tabela de Lançamentos Multi-usuário
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS lancamentos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            tipo TEXT NOT NULL,
            descricao TEXT NOT NULL,
            valor REAL NOT NULL,
            data_vencimento TEXT NOT NULL,
            categoria TEXT DEFAULT 'Geral',
            conta TEXT DEFAULT 'Conta Principal',
            status TEXT DEFAULT 'Realizado',
            protocolo TEXT,
            data_pagamento TEXT,
            tributavel INTEGER DEFAULT 0,
            dedutivel INTEGER DEFAULT 0,
            origem TEXT DEFAULT 'Manual'
        )
    ''')
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_lancamentos_user ON lancamentos(user_id, data_vencimento)")
    
    # Adicionar colunas se não existirem
    for col, col_def in [
        ('protocolo', 'TEXT'),
        ('data_pagamento', 'TEXT'),
        ('tributavel', 'INTEGER DEFAULT 0'),
        ('dedutivel', 'INTEGER DEFAULT 0'),
        ('origem', "TEXT DEFAULT 'Manual'")
    ]:
        try:
            cursor.execute(f"ALTER TABLE lancamentos ADD COLUMN {col} {col_def}")
        except sqlite3.OperationalError:
            pass
            
    # Tabela de Patrimônio / Ativos por usuário
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS patrimonio (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            ativo TEXT NOT NULL,
            saldo REAL NOT NULL DEFAULT 0.0,
            data_atualizacao TEXT NOT NULL,
            UNIQUE(user_id, ativo)
        )
    ''')
    
    # Tabela de Histórico de Patrimônio por usuário (Evolução no Tempo)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS historico_patrimonio (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            data_registro TEXT NOT NULL,
            total REAL NOT NULL,
            UNIQUE(user_id, data_registro)
        )
    ''')
    
    # Tabela de Saldo Inicial por Banco/Ano por usuário
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS saldo_inicial (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            banco TEXT NOT NULL,
            ano INTEGER NOT NULL,
            valor REAL NOT NULL,
            UNIQUE(user_id, banco, ano)
        )
    ''')
    
    conn.commit()
    conn.close()

# ----------------- LANÇAMENTOS -----------------

def adicionar_lancamento(user_id, tipo, descricao, valor, data_vencimento, categoria="Geral", conta="Conta Principal", status="Realizado", dedutivel=0, tributavel=0, origem="Manual", protocolo=None, data_pagamento=None, **kwargs):
    init_db()
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    if 'categoria_503020' in kwargs and (categoria == "Geral" or not categoria):
        categoria = kwargs['categoria_503020']
    if 'banco' in kwargs and (conta == "Conta Principal" or not conta):
        conta = kwargs['banco']
    cursor.execute('''
        INSERT INTO lancamentos (
            user_id, tipo, descricao, valor, data_vencimento, 
            categoria, conta, status, dedutivel, tributavel, origem, protocolo, data_pagamento
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (user_id, tipo, descricao.strip(), abs(float(valor)), str(data_vencimento), categoria, conta, status, dedutivel, tributavel, origem, protocolo, data_pagamento))
    novo_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return novo_id

def inserir_lancamento(user_id, tipo, descricao, valor, data_vencimento, categoria="Geral", conta="Conta Principal", status="Realizado", protocolo=None, data_pagamento=None, tributavel=0, dedutivel=0, **kwargs):
    if 'categoria_503020' in kwargs and (categoria == "Geral" or not categoria):
        categoria = kwargs['categoria_503020']
    if 'banco' in kwargs and (conta == "Conta Principal" or not conta):
        conta = kwargs['banco']
    return adicionar_lancamento(user_id, tipo, descricao, valor, data_vencimento, categoria=categoria, conta=conta, status=status, protocolo=protocolo, data_pagamento=data_pagamento, tributavel=tributavel, dedutivel=dedutivel, origem="Manual")

def excluir_lancamento(user_id, lancamento_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM lancamentos WHERE id = ? AND user_id = ?", (lancamento_id, user_id))
    linhas = cursor.rowcount
    conn.commit()
    conn.close()
    return linhas > 0

def excluir_lancamento_protocolo(user_id, protocolo):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM lancamentos WHERE protocolo = ? AND user_id = ?", (protocolo, user_id))
    linhas = cursor.rowcount
    conn.commit()
    conn.close()
    return linhas > 0

def excluir_lancamentos_multiplos(user_id, lista_ids):
    if not lista_ids:
        return 0
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    placeholders = ','.join(['?'] * len(lista_ids))
    params = [user_id] + list(lista_ids)
    cursor.execute(f"DELETE FROM lancamentos WHERE user_id = ? AND id IN ({placeholders})", params)
    linhas = cursor.rowcount
    conn.commit()
    conn.close()
    return linhas

def atualizar_categoria_lancamento(user_id, id_lancamento, nova_categoria):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("UPDATE lancamentos SET categoria = ? WHERE id = ? AND user_id = ?", (nova_categoria, id_lancamento, user_id))
    conn.commit()
    conn.close()

def atualizar_categorias_lote(user_id, lista_alteracoes):
    """lista_alteracoes: lista de tuplas (nova_categoria, id_lancamento)"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    for nova_cat, id_lanc in lista_alteracoes:
        cursor.execute("UPDATE lancamentos SET categoria = ? WHERE id = ? AND user_id = ?", (nova_cat, id_lanc, user_id))
    conn.commit()
    conn.close()

def carregar_lancamentos(user_id, ano=None, mes=None, categoria=None, tipo=None, conta=None):
    init_db()
    conn = sqlite3.connect(DB_NAME)
    
    query = "SELECT * FROM lancamentos WHERE user_id = ?"
    params = [user_id]
    
    if ano:
        query += " AND strftime('%Y', data_vencimento) = ?"
        params.append(str(ano))
    if mes:
        mes_fmt = f"{int(mes):02d}"
        query += " AND strftime('%m', data_vencimento) = ?"
        params.append(mes_fmt)
    if categoria and categoria != "Todas":
        query += " AND categoria = ?"
        params.append(categoria)
    if tipo and tipo != "Todos":
        query += " AND tipo = ?"
        params.append(tipo)
    if conta and conta != "Todas":
        query += " AND conta = ?"
        params.append(conta)
        
    query += " ORDER BY data_vencimento DESC, id DESC"
    
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    if not df.empty:
        if 'categoria_503020' not in df.columns and 'categoria' in df.columns:
            df['categoria_503020'] = df['categoria']
        if 'banco' not in df.columns and 'conta' in df.columns:
            df['banco'] = df['conta']
    return df

def listar_lancamentos(user_id=None):
    init_db()
    conn = sqlite3.connect(DB_NAME)
    if user_id is not None:
        df = pd.read_sql_query("SELECT * FROM lancamentos WHERE user_id = ? ORDER BY data_vencimento DESC, id DESC", conn, params=[user_id])
    else:
        df = pd.read_sql_query("SELECT * FROM lancamentos ORDER BY data_vencimento DESC, id DESC", conn)
    conn.close()
    if not df.empty:
        if 'categoria_503020' not in df.columns and 'categoria' in df.columns:
            df['categoria_503020'] = df['categoria']
        if 'banco' not in df.columns and 'conta' in df.columns:
            df['banco'] = df['conta']
    return df

def obter_resumo_kpis(user_id, ano=None, mes=None):
    df = carregar_lancamentos(user_id, ano=ano, mes=mes)
    if df.empty:
        return {
            "total_receitas": 0.0,
            "total_despesas": 0.0,
            "saldo_liquido": 0.0,
            "taxa_poupanca": 0.0,
            "qtd_lancamentos": 0
        }
        
    receitas = df[df["tipo"] == "Receita"]["valor"].sum()
    despesas = df[df["tipo"] == "Despesa"]["valor"].sum()
    saldo = receitas - despesas
    taxa_poupanca = ((saldo / receitas) * 100) if receitas > 0 else 0.0
    
    return {
        "total_receitas": float(receitas),
        "total_despesas": float(despesas),
        "saldo_liquido": float(saldo),
        "taxa_poupanca": float(taxa_poupanca),
        "qtd_lancamentos": len(df)
    }

# ----------------- PATRIMÔNIO & ATIVOS -----------------

def zerar_patrimonio(user_id):
    init_db()
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM patrimonio WHERE user_id = ?", (user_id,))
    cursor.execute("DELETE FROM historico_patrimonio WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()

def listar_patrimonio(user_id):
    init_db()
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Se NÃO for o usuário demo (user_id != 1), apaga automaticamente quaisquer ativos legados de teste (R$ 92.500)
    if user_id != 1:
        cursor.execute("SELECT COUNT(*) FROM patrimonio WHERE user_id = ? AND ativo IN ('Conta Corrente / Caixa', 'Reserva de Emergência (CDI)', 'Renda Fixa IPCA+ / Tesouro', 'Fundos Imobiliários (FIIs)', 'Ações Nacionais (B3)', 'Ações Brasil / Exterior', 'Previdência Privada', 'FGTS / Benefícios')", (user_id,))
        count_amostras = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM patrimonio WHERE user_id = ?", (user_id,))
        count_total = cursor.fetchone()[0]
        if count_amostras > 0 and (count_amostras == count_total or count_total <= 7):
            cursor.execute("DELETE FROM patrimonio WHERE user_id = ? AND ativo IN ('Conta Corrente / Caixa', 'Reserva de Emergência (CDI)', 'Renda Fixa IPCA+ / Tesouro', 'Fundos Imobiliários (FIIs)', 'Ações Nacionais (B3)', 'Ações Brasil / Exterior', 'Previdência Privada', 'FGTS / Benefícios')", (user_id,))
            cursor.execute("DELETE FROM historico_patrimonio WHERE user_id = ?", (user_id,))
            conn.commit()
            
    # Se for o usuário de demonstração (demo, user_id == 1) e não tiver ativos, insere os de amostra
    cursor.execute('SELECT COUNT(*) FROM patrimonio WHERE user_id = ?', (user_id,))
    if cursor.fetchone()[0] == 0 and user_id == 1:
        ativos_padrao = [
            ("Conta Corrente / Caixa", 2500.0),
            ("Reserva de Emergência (CDI)", 15000.0),
            ("Renda Fixa IPCA+ / Tesouro", 22000.0),
            ("Fundos Imobiliários (FIIs)", 18500.0),
            ("Ações Nacionais (B3)", 14000.0),
            ("Previdência Privada", 12000.0),
            ("FGTS / Benefícios", 8500.0)
        ]
        hoje_str = datetime.now().strftime("%Y-%m-%d")
        for atv, sld in ativos_padrao:
            cursor.execute('INSERT OR IGNORE INTO patrimonio (user_id, ativo, saldo, data_atualizacao) VALUES (?, ?, ?, ?)', (user_id, atv, sld, hoje_str))
        conn.commit()
        
    df = pd.read_sql_query("SELECT * FROM patrimonio WHERE user_id = ? ORDER BY id ASC", conn, params=[user_id])
    conn.close()
    return df

def atualizar_patrimonio(user_id, ativo, novo_saldo, data_atualizacao=None):
    init_db()
    if data_atualizacao is None:
        data_atualizacao = datetime.now().strftime("%Y-%m-%d")
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE patrimonio 
        SET saldo = ?, data_atualizacao = ?
        WHERE user_id = ? AND ativo = ?
    ''', (float(novo_saldo), str(data_atualizacao), user_id, ativo))
    conn.commit()
    conn.close()

def adicionar_ativo(user_id, nome_ativo, saldo=0.0):
    init_db()
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    hoje_str = datetime.now().strftime("%Y-%m-%d")
    try:
        cursor.execute('INSERT INTO patrimonio (user_id, ativo, saldo, data_atualizacao) VALUES (?, ?, ?, ?)', (user_id, nome_ativo.strip(), float(saldo), hoje_str))
        conn.commit()
    except sqlite3.IntegrityError:
        pass
    conn.close()

def excluir_ativo(user_id, nome_ativo):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM patrimonio WHERE user_id = ? AND ativo = ?', (user_id, nome_ativo))
    conn.commit()
    conn.close()

# ----------------- HISTÓRICO DE PATRIMÔNIO (1º DIA DO MÊS) -----------------

def registrar_historico_patrimonio(user_id, total, data_registro=None):
    init_db()
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
    cursor.execute("SELECT id FROM historico_patrimonio WHERE user_id = ? AND (data_registro LIKE ? OR data_registro = ?)", (user_id, f"{mes_ano}%", data_mes))
    rows = cursor.fetchall()
    if rows:
        primeiro_id = rows[0][0]
        cursor.execute("UPDATE historico_patrimonio SET data_registro = ?, total = ? WHERE id = ? AND user_id = ?", (data_mes, float(total), primeiro_id, user_id))
        if len(rows) > 1:
            outros_ids = [r[0] for r in rows[1:]]
            cursor.execute(f"DELETE FROM historico_patrimonio WHERE user_id = ? AND id IN ({','.join(['?']*len(outros_ids))})", [user_id] + outros_ids)
    else:
        cursor.execute("INSERT INTO historico_patrimonio (user_id, data_registro, total) VALUES (?, ?, ?)", (user_id, data_mes, float(total)))
        
    conn.commit()
    conn.close()

def listar_historico_patrimonio(user_id):
    init_db()
    conn = sqlite3.connect(DB_NAME)
    
    # Se usuário for o demo (user_id == 1) e não tiver histórico, injeta dados de amostra
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM historico_patrimonio WHERE user_id = ?", (user_id,))
    if cursor.fetchone()[0] == 0 and user_id == 1:
        amostras = [
            ("2026-01-01", 62000.0),
            ("2026-02-01", 66500.0),
            ("2026-03-01", 71000.0),
            ("2026-04-01", 75800.0),
            ("2026-05-01", 81200.0),
            ("2026-06-01", 85000.0),
            ("2026-07-01", 89400.0),
            ("2026-08-01", 92500.0)
        ]
        for dt_str, tot in amostras:
            cursor.execute("INSERT OR IGNORE INTO historico_patrimonio (user_id, data_registro, total) VALUES (?, ?, ?)", (user_id, dt_str, tot))
        conn.commit()
        
    df = pd.read_sql_query("SELECT * FROM historico_patrimonio WHERE user_id = ? ORDER BY data_registro ASC", conn, params=[user_id])
    conn.close()
    if not df.empty:
        df['competencia_mes'] = pd.to_datetime(df['data_registro']).dt.strftime('%Y-%m-01')
        df = df.groupby('competencia_mes', as_index=False).agg({'id': 'last', 'total': 'last'})
        df['data_registro'] = df['competencia_mes']
        df = df.sort_values('data_registro').reset_index(drop=True)
    return df

def excluir_historico_patrimonio(user_id, id_hist):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM historico_patrimonio WHERE id = ? AND user_id = ?", (id_hist, user_id))
    conn.commit()
    conn.close()

# ----------------- SALDO INICIAL -----------------

def obter_saldo_inicial(user_id, banco="Itaú", ano=2026):
    init_db()
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT valor FROM saldo_inicial WHERE user_id = ? AND banco = ? AND ano = ?", (user_id, banco, ano))
    row = cursor.fetchone()
    conn.close()
    return float(row[0]) if row and row[0] is not None else 0.0

def salvar_saldo_inicial(user_id, banco, ano, valor):
    init_db()
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM saldo_inicial WHERE user_id = ? AND banco = ? AND ano = ?", (user_id, banco, ano))
    row = cursor.fetchone()
    if row:
        cursor.execute("UPDATE saldo_inicial SET valor = ? WHERE id = ?", (float(valor), row[0]))
    else:
        cursor.execute("INSERT INTO saldo_inicial (user_id, banco, ano, valor) VALUES (?, ?, ?, ?)", (user_id, banco, ano, float(valor)))
    conn.commit()
    conn.close()

# ----------------- IMPORTADOR CSV -----------------

def processar_e_importar_csv(user_id, arquivo_upload, conta_padrao="Conta Principal"):
    init_db()
    try:
        content = arquivo_upload.getvalue().decode('utf-8', errors='replace')
        df = pd.read_csv(io.StringIO(content), sep=None, engine='python')
    except Exception as e:
        return False, f"Erro ao ler o arquivo CSV: {str(e)}", 0

    col_map = {c.lower().strip(): c for c in df.columns}
    
    col_data = None
    for cand in ['data', 'date', 'data lancamento', 'data_lancamento', 'dt', 'data vencimento']:
        if cand in col_map:
            col_data = col_map[cand]
            break
            
    col_desc = None
    for cand in ['descricao', 'historico', 'description', 'titulo', 'lancamento', 'detalhes', 'memo']:
        if cand in col_map:
            col_desc = col_map[cand]
            break

    col_valor = None
    for cand in ['valor', 'amount', 'montante', 'valor (r$)', 'valor r$', 'quantia']:
        if cand in col_map:
            col_valor = col_map[cand]
            break

    col_cat = None
    for cand in ['categoria', 'category', 'classificacao', 'tag']:
        if cand in col_map:
            col_cat = col_map[cand]
            break

    if not col_data or not col_desc or not col_valor:
        cols_encontradas = list(df.columns)
        return False, f"Não foi possível identificar colunas de Data, Descrição e Valor. Colunas encontradas: {cols_encontradas}", 0

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    importados = 0

    for _, row in df.iterrows():
        try:
            val_raw = str(row[col_valor]).strip()
            if not val_raw or val_raw.lower() == 'nan':
                continue
                
            val_clean = val_raw.replace("R$", "").replace(" ", "")
            if "," in val_clean and "." in val_clean:
                val_clean = val_clean.replace(".", "").replace(",", ".")
            elif "," in val_clean:
                val_clean = val_clean.replace(",", ".")
                
            valor_float = float(val_clean)
            tipo = "Receita" if valor_float > 0 else "Despesa"
            valor_abs = abs(valor_float)
            
            data_raw = str(row[col_data]).strip()
            data_formatada = datetime.now().strftime("%Y-%m-%d")
            
            for fmt in ['%d/%m/%Y', '%Y-%m-%d', '%d-%m-%Y', '%d/%m/%y', '%Y/%m/%d']:
                try:
                    dt_obj = datetime.strptime(data_raw.split(" ")[0], fmt)
                    data_formatada = dt_obj.strftime("%Y-%m-%d")
                    break
                except Exception:
                    pass

            desc = str(row[col_desc]).strip()
            categoria = "Outros"
            if col_cat and pd.notna(row[col_cat]):
                categoria = str(row[col_cat]).strip()
            else:
                desc_lower = desc.lower()
                if any(k in desc_lower for k in ['ifood', 'restaurante', 'padaria', 'supermercado', 'mercado', 'alimentacao']):
                    categoria = "Alimentação"
                elif any(k in desc_lower for k in ['uber', '99', 'posto', 'combustivel', 'gasolina', 'estacionamento']):
                    categoria = "Transporte"
                elif any(k in desc_lower for k in ['farmacia', 'drogaria', 'medico', 'consulta', 'hospital']):
                    categoria = "Saúde"
                elif any(k in desc_lower for k in ['aluguel', 'condominio', 'luz', 'energia', 'agua', 'internet', 'claro', 'vivo']):
                    categoria = "Moradia"
                elif any(k in desc_lower for k in ['netflix', 'spotify', 'cinema', 'show', 'lazer', 'steam']):
                    categoria = "Lazer"
                elif any(k in desc_lower for k in ['salario', 'ted recebida', 'pix recebido', 'rendimento', 'pro-labore']):
                    categoria = "Receita Principal"

            cursor.execute('''
                INSERT INTO lancamentos (
                    user_id, tipo, descricao, valor, data_vencimento,
                    categoria, conta, status, origem
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (user_id, tipo, desc, valor_abs, data_formatada, categoria, conta_padrao, "Realizado", "CSV"))
            importados += 1
            
        except Exception:
            continue

    conn.commit()
    conn.close()
    
    if importados == 0:
        return False, "Nenhum registro válido pôde ser importado do arquivo.", 0
        
    return True, f"Sucesso! {importados} transações foram importadas com sucesso.", importados

init_db()
