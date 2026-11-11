import os
import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime, date
import io
import re

DB_NAME = os.path.join(os.path.dirname(os.path.abspath(__file__)), "financas_comercial.db")

SUBCATEGORIAS_DESPESAS = [
    "🍽️ Alimentação & Delivery",
    "🛒 Supermercado & Feira",
    "🏠 Moradia & Contas",
    "🚗 Transporte & Combustível",
    "💊 Saúde & Farmácia",
    "🎓 Educação & Cursos",
    "🎉 Lazer & Entretenimento",
    "🛍️ Compras & Vestuário",
    "💅 Beleza & Cuidados Pessoais",
    "📱 Assinaturas & Serviços",
    "✈️ Viagens & Hospedagem",
    "🐾 Pets",
    "🏛️ Impostos & Taxas",
    "📈 Aportes & Patrimônio",
    "📋 Outros"
]

SUBCATEGORIAS_RECEITAS = [
    "💼 Salário / Pró-Labore",
    "🏛️ Benefício / INSS",
    "📈 Rendimentos & Dividendos",
    "🔄 Resgate de Aplicação",
    "💡 Renda Extra / Freelance",
    "↩️ Estorno / Reembolso",
    "📋 Outras Entradas"
]

TODAS_SUBCATEGORIAS = SUBCATEGORIAS_DESPESAS + [s for s in SUBCATEGORIAS_RECEITAS if s not in SUBCATEGORIAS_DESPESAS]

MAPA_SUBCATEGORIA_503020 = {
    "🍽️ Alimentação & Delivery": "Desejo (30%)",
    "🛒 Supermercado & Feira": "Necessidade (50%)",
    "🏠 Moradia & Contas": "Necessidade (50%)",
    "🚗 Transporte & Combustível": "Necessidade (50%)",
    "💊 Saúde & Farmácia": "Necessidade (50%)",
    "🎓 Educação & Cursos": "Necessidade (50%)",
    "🎉 Lazer & Entretenimento": "Desejo (30%)",
    "🛍️ Compras & Vestuário": "Desejo (30%)",
    "💅 Beleza & Cuidados Pessoais": "Desejo (30%)",
    "📱 Assinaturas & Serviços": "Desejo (30%)",
    "✈️ Viagens & Hospedagem": "Desejo (30%)",
    "🐾 Pets": "Necessidade (50%)",
    "🏛️ Impostos & Taxas": "Necessidade (50%)",
    "📈 Aportes & Patrimônio": "Investimento (20%)",
    "📋 Outros": "Desejo (30%)",
    "💼 Salário / Pró-Labore": "Renda (Não se aplica)",
    "🏛️ Benefício / INSS": "Renda (Não se aplica)",
    "📈 Rendimentos & Dividendos": "Renda (Não se aplica)",
    "🔄 Resgate de Aplicação": "Investimento (20%)",
    "💡 Renda Extra / Freelance": "Renda (Não se aplica)",
    "↩️ Estorno / Reembolso": "Renda (Não se aplica)",
    "📋 Outras Entradas": "Renda (Não se aplica)"
}

def inferir_subcategoria_icone(descricao, tipo="Despesa", categoria_503020=""):
    d = str(descricao or "").upper()
    t = str(tipo or "Despesa")
    c = str(categoria_503020 or "")

    if t in ["Receita", "Outras Receitas", "Resgate de Investimento", "Informativo"]:
        if t == "Resgate de Investimento" or any(k in d for k in ["RESGATE", "CDB", "TESOURO"]):
            return "🔄 Resgate de Aplicação"
        if any(k in d for k in ["INSS", "BENEFICIO", "BENEFÍCIO", "APOSENTADORIA"]):
            return "🏛️ Benefício / INSS"
        if any(k in d for k in ["SALARIO", "SALÁRIO", "PRO-LABORE", "PRÓ-LABORE", "CAIXA SEGURADORA", "EMANUELA"]):
            return "💼 Salário / Pró-Labore"
        if any(k in d for k in ["ESTORNO", "CANCELAMENTO", "REEMBOLSO"]):
            return "↩️ Estorno / Reembolso"
        if any(k in d for k in ["DIVIDENDO", "RENDIMENTO", "JUROS", "FII"]):
            return "📈 Rendimentos & Dividendos"
        return "💡 Renda Extra / Freelance" if t == "Outras Receitas" else "💼 Salário / Pró-Labore"

    if any(k in d for k in ["SUPERMERCADO", "ATACAD", "MERCADO", "COMPRA CARNE", "ASSAI", "CARREFOUR", "PAO DE ACUCAR", "FEIRA", "HORTIFRUTI"]):
        return "🛒 Supermercado & Feira"
    if any(k in d for k in ["IFOOD", "RESTAURANTE", "PADARIA", "PANIF", "LANCHE", "BURGER", "PIZZA", "CHURR", "SORVE", "BACIO", "CAFE", "CAFÉ", "BAR ", "OUTBACK", "COCO BAMBU", "ALIMENTACAO"]):
        return "🍽️ Alimentação & Delivery"
    if any(k in d for k in ["EQUATORIAL", "ENERGIA", "LUZ", "SANEAGO", "AGUA", "ÁGUA", "GUA", "HABITACAO", "HABITAÇÃO", "CAIXA - HAB", "GCI CAIXA", "CONDOMINIO", "CONDOMÍNIO", "ALUGUEL", "FAXINA", "DANIELA", "INTERNET", "DLS NET", "VERO", "VIVO", "CLARO", "TIM", "MORADIA"]):
        return "🏠 Moradia & Contas"
    if any(k in d for k in ["UBER", "99", "GASOLINA", "ABASTECE", "COMBUSTIVEL", "COMBUSTÍVEL", "POSTO", "ESTACIONAMENTO", "PEDAGIO", "PEDÁGIO", "BANCO GM", "MONTANA", "FINANCIAMENTO", "OFICINA", "PNEU", "YOUSE", "SEGURO AUTO", "TRANSPORTE"]):
        return "🚗 Transporte & Combustível"
    if any(k in d for k in ["PSIQUIATRA", "MEDIC", "MÉDIC", "MDIC", "CONSULTA", "EXAME", "HOSPITAL", "CLINICA", "CLÍNICA", "DROGA", "FARMACIA", "FARMÁCIA", "DROGASIL", "RAIA", "PAGUE MENOS", "UNIMED", "ODONTO", "DENTISTA", "SAUDE", "SAÚDE"]):
        return "💊 Saúde & Farmácia"
    if any(k in d for k in ["ESCOLA", "ALANNA", "FACULDADE", "CURSO", "EBPOS", "POS GRADU", "PÓS GRADU", "EDITORA", "LIVRO", "COLEGIO", "COLÉGIO", "EDUCACAO", "EDUCAÇÃO"]):
        return "🎓 Educação & Cursos"
    if any(k in d for k in ["APLICACAO", "APLICAÇÃO", "CDB", "LOTE", "URBANISMO", "G10", "COFRINHO", "TESOURO", "POUPAN", "INVESTIMENTO"]) or c == "Investimento (20%)":
        return "📈 Aportes & Patrimônio"
    if any(k in d for k in ["IPTU", "IPVA", "DETRAN", "SEFAZ", "DARF", "DAR ", "DAS MEI", "RECEITA FED", "MULTA", "DNIT", "CRC", "CONSELHO", "IMPOSTO", "TAXA"]):
        return "🏛️ Impostos & Taxas"
    if any(k in d for k in ["HOTEL", "VIAGEM", "PASSAGEM", "LATAM", "AZUL", "GOL", "AIRBNB", "BOOKING", "DECOLAR"]):
        return "✈️ Viagens & Hospedagem"
    if any(k in d for k in ["PET", "VET", "RACAO", "RAÇÃO", "COBASI", "PETZ"]):
        return "🐾 Pets"
    if any(k in d for k in ["SALAO", "SALÃO", "BELEZA", "ESTETICA", "ESTÉTICA", "CABELO", "MANICURE", "BARBEARIA", "PERFUME", "BOTICARIO", "NATURA", "SEPHORA"]):
        return "💅 Beleza & Cuidados Pessoais"
    if any(k in d for k in ["NETFLIX", "SPOTIFY", "MICROSOFT", "GOOGLE", "APPLE", "PRIME", "DISNEY", "HBO", "YOUTUBE", "CHATGPT", "OPENAI", "ASSINATURA", "CLOUD"]):
        return "📱 Assinaturas & Serviços"
    if any(k in d for k in ["RENNER", "RIACHUELO", "CEA", "ZARA", "SHOP", "SHPP", "SHOPEE", "AMAZON", "MERCADO LIVRE", "MAGALU", "ALIEXPRESS", "SHEIN", "MODA", "VESTUARIO", "CALCADO", "CALÇADO", "ROUPA", "LOJA"]):
        return "🛍️ Compras & Vestuário"
    if any(k in d for k in ["CINEMA", "PARK", "SHOW", "INGRESSO", "TEATRO", "LAZER", "CLUBE", "FESTA", "JOGO", "STEAM"]):
        return "🎉 Lazer & Entretenimento"

    if c == "Necessidade (50%)":
        return "🏠 Moradia & Contas"
    elif c == "Investimento (20%)":
        return "📈 Aportes & Patrimônio"
    return "📋 Outros"

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
            subcategoria TEXT DEFAULT '📋 Outros',
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
        ('origem', "TEXT DEFAULT 'Manual'"),
        ('subcategoria', "TEXT DEFAULT '📋 Outros'")
    ]:
        try:
            cursor.execute(f"ALTER TABLE lancamentos ADD COLUMN {col} {col_def}")
        except sqlite3.OperationalError:
            pass

    # Tabela de Metas/Tetos por Categoria por usuário
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS metas_categorias (
            user_id INTEGER NOT NULL,
            subcategoria TEXT NOT NULL,
            limite_mensal REAL NOT NULL,
            PRIMARY KEY (user_id, subcategoria)
        )
    ''')
            
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

    # Tabela de Sonhos & Caixinhas (Planejamento Futuro vinculado ao Patrimônio por usuário)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sonhos_metas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            titulo TEXT NOT NULL,
            icone TEXT NOT NULL DEFAULT '🎯',
            valor_alvo REAL NOT NULL,
            valor_atual REAL NOT NULL DEFAULT 0.0,
            ativo_vinculado TEXT,
            aporte_mensal_planejado REAL NOT NULL DEFAULT 0.0,
            data_limite TEXT,
            data_criacao TEXT NOT NULL
        )
    ''')
    
    conn.commit()
    conn.close()

# ----------------- LANÇAMENTOS -----------------

def adicionar_lancamento(user_id, tipo, descricao, valor, data_vencimento, categoria="Geral", conta="Conta Principal", status="Realizado", dedutivel=0, tributavel=0, origem="Manual", protocolo=None, data_pagamento=None, subcategoria=None, **kwargs):
    init_db()
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    if 'categoria_503020' in kwargs and (categoria == "Geral" or not categoria):
        categoria = kwargs['categoria_503020']
    if 'banco' in kwargs and (conta == "Conta Principal" or not conta):
        conta = kwargs['banco']
    if not subcategoria:
        subcategoria = inferir_subcategoria_icone(descricao, tipo, categoria)
    cursor.execute('''
        INSERT INTO lancamentos (
            user_id, tipo, descricao, valor, data_vencimento, 
            categoria, subcategoria, conta, status, dedutivel, tributavel, origem, protocolo, data_pagamento
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (user_id, tipo, descricao.strip(), abs(float(valor)), str(data_vencimento), categoria, subcategoria, conta, status, dedutivel, tributavel, origem, protocolo, data_pagamento))
    novo_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return novo_id

def inserir_lancamento(user_id, tipo, descricao, valor, data_vencimento, categoria="Geral", conta="Conta Principal", status="Realizado", protocolo=None, data_pagamento=None, tributavel=0, dedutivel=0, subcategoria=None, **kwargs):
    if 'categoria_503020' in kwargs and (categoria == "Geral" or not categoria):
        categoria = kwargs['categoria_503020']
    if 'banco' in kwargs and (conta == "Conta Principal" or not conta):
        conta = kwargs['banco']
    return adicionar_lancamento(user_id, tipo, descricao, valor, data_vencimento, categoria=categoria, conta=conta, status=status, protocolo=protocolo, data_pagamento=data_pagamento, tributavel=tributavel, dedutivel=dedutivel, subcategoria=subcategoria, origem="Manual")

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

def atualizar_categoria_lancamento(user_id, id_lancamento, nova_categoria, nova_subcategoria=None):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    if nova_subcategoria:
        cursor.execute("UPDATE lancamentos SET categoria = ?, subcategoria = ? WHERE id = ? AND user_id = ?", (nova_categoria, nova_subcategoria, id_lancamento, user_id))
    else:
        cursor.execute("UPDATE lancamentos SET categoria = ? WHERE id = ? AND user_id = ?", (nova_categoria, id_lancamento, user_id))
    conn.commit()
    conn.close()

def atualizar_categorias_lote(user_id, lista_alteracoes):
    """lista_alteracoes: lista de tuplas (nova_categoria, id_lancamento) ou (nova_categoria, nova_subcategoria, id_lancamento)"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    for item in lista_alteracoes:
        if len(item) == 3:
            nova_cat, nova_sub, id_lanc = item
            cursor.execute("UPDATE lancamentos SET categoria = ?, subcategoria = ? WHERE id = ? AND user_id = ?", (nova_cat, nova_sub, id_lanc, user_id))
        else:
            nova_cat, id_lanc = item
            cursor.execute("UPDATE lancamentos SET categoria = ? WHERE id = ? AND user_id = ?", (nova_cat, id_lanc, user_id))
    conn.commit()
    conn.close()

def atualizar_status_lote(user_id, lista_ids, novo_status="Pago"):
    if not lista_ids:
        return 0
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    placeholders = ','.join(['?'] * len(lista_ids))
    params = [novo_status, user_id] + [int(i) for i in lista_ids]
    cursor.execute(f"UPDATE lancamentos SET status = ? WHERE user_id = ? AND id IN ({placeholders})", params)
    linhas = cursor.rowcount
    conn.commit()
    conn.close()
    return linhas

def sincronizar_subcategorias_existentes():
    init_db()
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT id, descricao, tipo, categoria, subcategoria FROM lancamentos")
    rows = cursor.fetchall()
    atualizados = 0
    for r_id, desc, tipo, cat, subcat in rows:
        if not subcat or subcat in ['📋 Outros', 'Geral', 'Outros', '']:
            sug = inferir_subcategoria_icone(desc, tipo, cat)
            if sug != subcat:
                cursor.execute("UPDATE lancamentos SET subcategoria = ? WHERE id = ?", (sug, r_id))
                atualizados += 1
    conn.commit()
    conn.close()
    return atualizados

def listar_metas_categorias(user_id):
    init_db()
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT subcategoria, limite_mensal FROM metas_categorias WHERE user_id = ?", (user_id,))
    rows = cursor.fetchall()
    conn.close()
    return {r[0]: float(r[1]) for r in rows}

def salvar_meta_categoria(user_id, subcategoria, limite_mensal):
    init_db()
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    if float(limite_mensal) <= 0:
        cursor.execute("DELETE FROM metas_categorias WHERE user_id = ? AND subcategoria = ?", (user_id, subcategoria))
    else:
        cursor.execute('''
            INSERT INTO metas_categorias (user_id, subcategoria, limite_mensal)
            VALUES (?, ?, ?)
            ON CONFLICT(user_id, subcategoria) DO UPDATE SET limite_mensal = excluded.limite_mensal
        ''', (user_id, subcategoria, float(limite_mensal)))
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
        if 'subcategoria' not in df.columns:
            df['subcategoria'] = df.apply(lambda r: inferir_subcategoria_icone(r.get('descricao', ''), r.get('tipo', 'Despesa'), r.get('categoria_503020', '')), axis=1)
        else:
            df['subcategoria'] = df.apply(
                lambda r: inferir_subcategoria_icone(r.get('descricao', ''), r.get('tipo', 'Despesa'), r.get('categoria_503020', ''))
                if pd.isna(r.get('subcategoria')) or str(r.get('subcategoria')).strip() in ['', 'None', 'nan']
                else r.get('subcategoria'),
                axis=1
            )
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
        if 'subcategoria' not in df.columns:
            df['subcategoria'] = df.apply(lambda r: inferir_subcategoria_icone(r.get('descricao', ''), r.get('tipo', 'Despesa'), r.get('categoria_503020', '')), axis=1)
        else:
            df['subcategoria'] = df.apply(
                lambda r: inferir_subcategoria_icone(r.get('descricao', ''), r.get('tipo', 'Despesa'), r.get('categoria_503020', ''))
                if pd.isna(r.get('subcategoria')) or str(r.get('subcategoria')).strip() in ['', 'None', 'nan']
                else r.get('subcategoria'),
                axis=1
            )
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
    # Sincroniza automaticamente qualquer Sonho/Caixinha vinculado a este ativo
    cursor.execute('''
        UPDATE sonhos_metas
        SET valor_atual = ?
        WHERE user_id = ? AND ativo_vinculado = ?
    ''', (float(novo_saldo), user_id, ativo))
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

# ----------------- SONHOS & CAIXINHAS (PLANEJAMENTO FUTURO) -----------------

ICONES_SONHOS = [
    "🏠 Casa Própria / Imóvel",
    "🚗 Carro / Moto Nova",
    "📺 TV Nova / Eletrônicos",
    "✈️ Viagem dos Sonhos",
    "🛡️ Reserva de Emergência",
    "🎓 Pós-Graduação / Estudos",
    "💍 Casamento / Festa",
    "💻 Notebook / Setup Trabalho",
    "🛋️ Reforma / Móveis Planejados",
    "🎯 Outro Sonho / Meta"
]

def listar_sonhos(user_id):
    init_db()
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    # Sincronizar valor_atual com o saldo do ativo_vinculado no patrimônio (se existir)
    cursor.execute('''
        UPDATE sonhos_metas
        SET valor_atual = (
            SELECT p.saldo FROM patrimonio p WHERE p.user_id = sonhos_metas.user_id AND p.ativo = sonhos_metas.ativo_vinculado
        )
        WHERE user_id = ? AND ativo_vinculado IS NOT NULL AND ativo_vinculado != ''
          AND EXISTS (SELECT 1 FROM patrimonio p WHERE p.user_id = sonhos_metas.user_id AND p.ativo = sonhos_metas.ativo_vinculado)
    ''', (user_id,))
    conn.commit()
    df = pd.read_sql_query("SELECT * FROM sonhos_metas WHERE user_id = ? ORDER BY id ASC", conn, params=[user_id])
    conn.close()
    return df

def criar_sonho(user_id, titulo, icone, valor_alvo, valor_inicial=0.0, ativo_vinculado="", aporte_mensal_planejado=0.0, data_limite="", criar_caixinha_patrimonio=True):
    init_db()
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    hoje_str = datetime.now().strftime("%Y-%m-%d")
    titulo_limpo = titulo.strip()

    if criar_caixinha_patrimonio and (not ativo_vinculado or ativo_vinculado == "✨ Criar Nova Caixinha no Patrimônio"):
        nome_caixinha = f"Caixinha: {titulo_limpo}"
        ativo_vinculado = nome_caixinha
        cursor.execute('SELECT saldo FROM patrimonio WHERE user_id = ? AND ativo = ?', (user_id, nome_caixinha))
        row_pat = cursor.fetchone()
        if row_pat is None:
            cursor.execute(
                'INSERT INTO patrimonio (user_id, ativo, saldo, data_atualizacao) VALUES (?, ?, ?, ?)',
                (user_id, nome_caixinha, float(valor_inicial), hoje_str)
            )
        else:
            if float(valor_inicial) > 0:
                cursor.execute(
                    'UPDATE patrimonio SET saldo = ?, data_atualizacao = ? WHERE user_id = ? AND ativo = ?',
                    (float(valor_inicial), hoje_str, user_id, nome_caixinha)
                )
    elif ativo_vinculado and ativo_vinculado != "Não vincular":
        cursor.execute('SELECT saldo FROM patrimonio WHERE user_id = ? AND ativo = ?', (user_id, ativo_vinculado))
        row_pat = cursor.fetchone()
        if row_pat is not None and float(valor_inicial) == 0.0:
            valor_inicial = float(row_pat[0])
    else:
        ativo_vinculado = ""

    cursor.execute('''
        INSERT INTO sonhos_metas (
            user_id, titulo, icone, valor_alvo, valor_atual, ativo_vinculado,
            aporte_mensal_planejado, data_limite, data_criacao
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        user_id, titulo_limpo, icone, float(valor_alvo), float(valor_inicial),
        ativo_vinculado, float(aporte_mensal_planejado), str(data_limite or ""), hoje_str
    ))

    cursor.execute("SELECT SUM(saldo) FROM patrimonio WHERE user_id = ?", (user_id,))
    tot_pat = cursor.fetchone()[0] or 0.0
    conn.commit()
    conn.close()
    if tot_pat > 0:
        registrar_historico_patrimonio(user_id, tot_pat, hoje_str)

def aportar_sonho(user_id, id_sonho, valor_aporte, registrar_lancamento=True, banco="Itaú", data_aporte=None):
    """Realiza um aporte na Caixinha do Sonho, atualiza o ativo no Patrimônio e retorna os indicadores de progresso e % que falta."""
    init_db()
    if data_aporte is None:
        data_aporte = datetime.now().strftime("%Y-%m-%d")
    elif isinstance(data_aporte, (date, datetime)):
        data_aporte = data_aporte.strftime("%Y-%m-%d")

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT titulo, icone, valor_alvo, valor_atual, ativo_vinculado FROM sonhos_metas WHERE id = ? AND user_id = ?",
        (int(id_sonho), user_id)
    )
    row = cursor.fetchone()
    if not row:
        conn.close()
        return None

    titulo, icone, valor_alvo, valor_atual, ativo_vinculado = row
    novo_valor = float(valor_atual) + float(valor_aporte)

    cursor.execute("UPDATE sonhos_metas SET valor_atual = ? WHERE id = ? AND user_id = ?", (novo_valor, int(id_sonho), user_id))

    if ativo_vinculado:
        cursor.execute("SELECT saldo FROM patrimonio WHERE user_id = ? AND ativo = ?", (user_id, ativo_vinculado))
        r_pat = cursor.fetchone()
        if r_pat is not None:
            novo_saldo_pat = float(r_pat[0]) + float(valor_aporte)
            cursor.execute(
                "UPDATE patrimonio SET saldo = ?, data_atualizacao = ? WHERE user_id = ? AND ativo = ?",
                (novo_saldo_pat, str(data_aporte), user_id, ativo_vinculado)
            )
            cursor.execute(
                "UPDATE sonhos_metas SET valor_atual = ? WHERE user_id = ? AND ativo_vinculado = ?",
                (novo_saldo_pat, user_id, ativo_vinculado)
            )
            novo_valor = novo_saldo_pat
        else:
            cursor.execute(
                "INSERT INTO patrimonio (user_id, ativo, saldo, data_atualizacao) VALUES (?, ?, ?, ?)",
                (user_id, ativo_vinculado, novo_valor, str(data_aporte))
            )

    cursor.execute("SELECT SUM(saldo) FROM patrimonio WHERE user_id = ?", (user_id,))
    tot_pat = cursor.fetchone()[0] or 0.0
    conn.commit()
    conn.close()

    if tot_pat > 0:
        registrar_historico_patrimonio(user_id, tot_pat, str(data_aporte))

    if registrar_lancamento and float(valor_aporte) > 0:
        import uuid
        adicionar_lancamento(
            user_id=user_id,
            tipo="Despesa",
            descricao=f"Aporte Caixinha: {titulo}",
            valor=float(valor_aporte),
            data_vencimento=str(data_aporte),
            categoria="Investimento (20%)",
            subcategoria="📈 Aportes & Patrimônio",
            conta=banco or "Itaú",
            status="Pago",
            protocolo=f"SONHO-{str(uuid.uuid4())[:6].upper()}",
            data_pagamento=str(data_aporte),
            tributavel=0,
            dedutivel=0,
            origem="Caixinha Sonho"
        )

    valor_alvo_f = max(float(valor_alvo), 0.01)
    pct_atingido = min((novo_valor / valor_alvo_f) * 100.0, 100.0)
    pct_falta = max(100.0 - pct_atingido, 0.0)
    valor_falta = max(valor_alvo_f - novo_valor, 0.0)

    return {
        "titulo": titulo,
        "icone": icone,
        "valor_aporte": float(valor_aporte),
        "novo_valor": novo_valor,
        "valor_alvo": float(valor_alvo),
        "pct_atingido": pct_atingido,
        "pct_falta": pct_falta,
        "valor_falta": valor_falta,
        "ativo_vinculado": ativo_vinculado
    }

def excluir_sonho(user_id, id_sonho):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM sonhos_metas WHERE id = ? AND user_id = ?", (int(id_sonho), user_id))
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

            subcat_auto = inferir_subcategoria_icone(desc, tipo, categoria)
            cursor.execute('''
                INSERT INTO lancamentos (
                    user_id, tipo, descricao, valor, data_vencimento,
                    categoria, subcategoria, conta, status, origem
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (user_id, tipo, desc, valor_abs, data_formatada, categoria, subcat_auto, conta_padrao, "Realizado", "CSV"))
            importados += 1
            
        except Exception:
            continue

    conn.commit()
    conn.close()
    
    if importados == 0:
        return False, "Nenhum registro válido pôde ser importado do arquivo.", 0
        
    return True, f"Sucesso! {importados} transações foram importadas com sucesso.", importados

init_db()
try:
    sincronizar_subcategorias_existentes()
except Exception:
    pass
