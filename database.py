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
            dedutivel INTEGER DEFAULT 0,
            subcategoria TEXT DEFAULT '📋 Outros'
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

    try:
        cursor.execute("ALTER TABLE lancamentos ADD COLUMN subcategoria TEXT DEFAULT '📋 Outros'")
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

    # Tabela de Metas de Gastos por Subcategoria (Estilo Apps Nota 5)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS metas_categorias (
            subcategoria TEXT PRIMARY KEY,
            limite_mensal REAL
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

# --- MAPA E CLASSIFICADOR AUTOMÁTICO DE SUBCATEGORIAS COM ÍCONES ---
SUBCATEGORIAS_DESPESAS = [
    "🏠 Moradia & Contas",
    "🛒 Supermercado & Padaria",
    "🍽️ Alimentação & Delivery",
    "🚗 Transporte & Combustível",
    "💊 Saúde & Farmácia",
    "🎓 Educação & Cursos",
    "🛍️ Compras & Vestuário",
    "✈️ Lazer & Viagens",
    "💄 Beleza & Bem-Estar",
    "💻 Assinaturas & Serviços",
    "🏛️ Impostos, Taxas & Seguros",
    "📈 Investimentos & Patrimônio",
    "🤝 Transferências & Pix",
    "📋 Outros"
]

SUBCATEGORIAS_RECEITAS = [
    "💼 Salário & Proventos",
    "🏛️ Benefício / INSS",
    "📈 Rendimentos & Dividendos",
    "💰 Resgate de Investimentos",
    "🔄 Pix / Reembolsos / Estornos",
    "📋 Outras Entradas"
]

TODAS_SUBCATEGORIAS = SUBCATEGORIAS_DESPESAS + [s for s in SUBCATEGORIAS_RECEITAS if s not in SUBCATEGORIAS_DESPESAS]

MAPA_SUBCATEGORIA_503020 = {
    "🏠 Moradia & Contas": "Necessidade (50%)",
    "🛒 Supermercado & Padaria": "Necessidade (50%)",
    "🍽️ Alimentação & Delivery": "Desejo (30%)",
    "🚗 Transporte & Combustível": "Necessidade (50%)",
    "💊 Saúde & Farmácia": "Necessidade (50%)",
    "🎓 Educação & Cursos": "Necessidade (50%)",
    "🛍️ Compras & Vestuário": "Desejo (30%)",
    "✈️ Lazer & Viagens": "Desejo (30%)",
    "💄 Beleza & Bem-Estar": "Desejo (30%)",
    "💻 Assinaturas & Serviços": "Desejo (30%)",
    "🏛️ Impostos, Taxas & Seguros": "Necessidade (50%)",
    "📈 Investimentos & Patrimônio": "Investimento (20%)",
    "🤝 Transferências & Pix": "Necessidade (50%)",
    "📋 Outros": "Necessidade (50%)",
    "💼 Salário & Proventos": "Renda (Não se aplica)",
    "🏛️ Benefício / INSS": "Renda (Não se aplica)",
    "📈 Rendimentos & Dividendos": "Renda (Não se aplica)",
    "💰 Resgate de Investimentos": "Investimento (20%)",
    "🔄 Pix / Reembolsos / Estornos": "Renda (Não se aplica)",
    "📋 Outras Entradas": "Renda (Não se aplica)"
}

def inferir_subcategoria_icone(descricao, tipo="Despesa", categoria_503020=None):
    """Infere automaticamente a subcategoria com ícone a partir da descrição e do tipo do lançamento."""
    d = str(descricao or "").upper()
    t = str(tipo or "Despesa").strip()
    cat50 = str(categoria_503020 or "").strip()

    # 1. Tratamento de Receitas / Resgates / Informativos de Renda
    if t in ["Receita", "Outras Receitas", "Resgate de Investimento"] or (t == "Informativo" and "RETIDO" not in d):
        if t == "Resgate de Investimento" or "RESGATE" in d:
            return "💰 Resgate de Investimentos"
        if any(k in d for k in ["INSS", "BENEFÍCIO", "BENEFICIO", "APOSENT", "PENSAO", "PENSÃO"]):
            return "🏛️ Benefício / INSS"
        if any(k in d for k in ["SALÁRIO", "SALARIO", "TED 104.0630", "CAIXA SEGURADORA", "PROVENTO", "REMUNERACAO"]):
            return "💼 Salário & Proventos"
        if any(k in d for k in ["REND PAGO", "APLIC AUT", "JSCP", "DIVIDEND", "BTC-JR", "RENDIMENTO"]):
            return "📈 Rendimentos & Dividendos"
        if any(k in d for k in ["PIX", "DEV ", "CANCELAMENTO", "ESTORNO", "REEMBOLSO", "TED "]):
            return "🔄 Pix / Reembolsos / Estornos"
        return "📋 Outras Entradas"

    # 2. Tratamento de Despesas (e Informativos de retenção)
    if any(k in d for k in ["APLICACAO CDB", "APLICAÇÃO CDB", "COFRINHO", "G10 URBANISMO", "LOTE J.LUX", "LOTE J. LUX", "TESOURO DIRETO"]):
        return "📈 Investimentos & Patrimônio"

    if any(k in d for k in [
        "DROGA", "FARMACIA", "FARMÁCIA", "PSIQUIATRA", "MÉDICA", "MEDICA", "MÉDICO", "MEDICO",
        "SAUDE", "SAÚDE", "RD SAUDE", "CLINICA", "CLÍNICA", "HOSPITAL", "LABORAT", "ODONTO", "ORTOLIFE"
    ]):
        return "💊 Saúde & Farmácia"

    if any(k in d for k in [
        "ESCOLA", "EDUCAC", "EDUCAÇ", "EBPOS", "POS GRAD", "PÓS GRAD", "GRAN ", "CURSO", "CURSOS",
        "MAPASDALULU", "MAPA CURSOS", "EDITORA", "LEITURA", "FACULDADE", "COLEGIO", "COLÉGIO", "KIWIFY", "HOTMART"
    ]):
        return "🎓 Educação & Cursos"

    if any(k in d for k in [
        "GASOLINA", "ABAST", "COMBUSTIVEL", "COMBUSTÍVEL", "POSTO", "IPIRANGA", "UBER", "99",
        "MONTANA", "BANCO GM", "PEDRAGON", "AUTO CENTRO", "BATERIA CAR", "PARK", "ACPARK", "QUALITY PETR"
    ]):
        return "🚗 Transporte & Combustível"

    if any(k in d for k in [
        "IPVA", "IPTU", "DETRAN", "SEFAZ", "RECEITA FED", "IRPF", "IRRF", "INSS RETIDO", "DAS MEI",
        "CRC", "CONSELHO REGIONAL", "TARIFA BANC", "IOF", "PREFEITURA", "MULTA", "DNIT", "YOUSE", "SEGURO", "SAFE COVER"
    ]):
        return "🏛️ Impostos, Taxas & Seguros"

    if any(k in d for k in [
        "ENERGIA", "EQUATORIAL", "ÁGUA", "AGUA", "SANEAGO", "HABITACAO", "HABITAÇÃO", "GCI CAIXA",
        "ALUGUEL", "CONDOMINIO", "CONDOMÍNIO", "FAXINA", "DANIELA_FAXINA", "VERO_INTERNET", "DLS NET",
        "INTERNET", "VIVO", "TELEFONICA", "CLARO", "TIM", "CELULAR", "COMPRA CAMA"
    ]):
        return "🏠 Moradia & Contas"

    if any(k in d for k in [
        "ATACAD", "FORT ", "COSTA ATACAD", "SUPERMERC", "MERCADO ", "ASSINATURA SAMS", "PANIF",
        "PADARIA", "PAOLEVE", "CASA SETE", "COMPRA CARNE", "COMER", "BSB L", "VALPARAISO C"
    ]):
        return "🛒 Supermercado & Padaria"

    if any(k in d for k in [
        "IFOOD", "RESTA", "BURGER", "CHURR", "SORVE", "BACIO", "CAFE", "CAFÉ", "DOCARIA",
        "KALZONE", "PANELINHA", "ALIMENTACAO", "ALIMENTAÇÃO", "PIZZA", "LANCHE", "SUSHI", "BAR "
    ]):
        return "🍽️ Alimentação & Delivery"

    if any(k in d for k in [
        "SMILES", "HOTEL", "VIAGEM", "VILA G", "CINEMA", "DIVERSAO", "DIVERSÃO", "LAZER",
        "INGRESSO", "SYSCASHTYCKET", "CLUB", "DECOLAR", "AIRBNB", "LATAM", "AZUL", "GOL "
    ]):
        return "✈️ Lazer & Viagens"

    if any(k in d for k in [
        "OBOTICARIO", "BOTICARIO", "BELEZA", "WELLHUB", "GYMPASS", "WEB DIET", "LETMEBE",
        "ESSENCIAS", "COSMETIC", "SALAO", "SALÃO", "ESTETICA", "ESTÉTICA", "ACADEMIA", "FITNESS", "RITUARIA"
    ]):
        return "💄 Beleza & Bem-Estar"

    if any(k in d for k in [
        "MICROSOFT", "GOOGLE", "OPENAI", "CHATGPT", "RUNWAY", "DEEZER", "SPOTIFY", "NETFLIX",
        "MELIMAIS", "AMAZON PRIME", "APPLE", "CANVA"
    ]):
        return "💻 Assinaturas & Serviços"

    if any(k in d for k in [
        "SHOPEE", "SHPP", "SHEIN", "MERCADOLIVRE", "MERCADO LIVRE", "RENNER", "RIACHUELO", "MARISA",
        "MAGALU", "MAGAZINELUIZA", "HAVAN", "AMERICANAS", "FUJIOKA", "TEMU", "MODA", "CONFECCOES",
        "CONFECÇÕES", "VESTUARIO", "SONHO DOS PES", "CALCADO", "CALÇADO", "POLO WEAR", "INOVATHI",
        "CRESCI E PERDI", "SHOPPING", "SHOP ", "SHOPP", "ATELIE", "AVIAME", "IMPORTADOS", "APPMAX"
    ]):
        return "🛍️ Compras & Vestuário"

    if any(k in d for k in ["PIX TRANSF", "PIX QRS", "TED ", "DOC "]):
        if cat50 == "Desejo (30%)":
            return "🛍️ Compras & Vestuário"
        return "🤝 Transferências & Pix"

    if cat50 == "Investimento (20%)":
        return "📈 Investimentos & Patrimônio"
    if cat50 == "Desejo (30%)":
        return "🛍️ Compras & Vestuário"

    return "📋 Outros"


def sincronizar_subcategorias_existentes():
    """Classifica automaticamente lançamentos que ainda não possuem subcategoria específica."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT id, tipo, descricao, categoria_503020, subcategoria FROM lancamentos")
    rows = cursor.fetchall()
    atualizacoes = []
    for row_id, tipo, desc, cat50, subcat_atual in rows:
        if not subcat_atual or subcat_atual in ("📋 Outros", "Outros", ""):
            nova_sub = inferir_subcategoria_icone(desc, tipo, cat50)
            if nova_sub != subcat_atual:
                atualizacoes.append((nova_sub, row_id))
    if atualizacoes:
        cursor.executemany("UPDATE lancamentos SET subcategoria = ? WHERE id = ?", atualizacoes)
        conn.commit()
    conn.close()
    return len(atualizacoes)


def inserir_lancamento(tipo, descricao, valor, data_vencimento, categoria_503020, banco, status, protocolo=None, data_pagamento=None, tributavel=0, dedutivel=0, subcategoria=None):
    if not subcategoria or subcategoria in ("📋 Outros", ""):
        subcategoria = inferir_subcategoria_icone(descricao, tipo, categoria_503020)
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO lancamentos (tipo, descricao, valor, data_vencimento, categoria_503020, banco, status, protocolo, data_pagamento, tributavel, dedutivel, subcategoria)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (tipo, descricao, valor, data_vencimento, categoria_503020, banco, status, protocolo, data_pagamento, tributavel, dedutivel, subcategoria))
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

def atualizar_categoria_lancamento(id_lancamento, nova_categoria, nova_subcategoria=None):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    if nova_subcategoria is not None:
        cursor.execute('UPDATE lancamentos SET categoria_503020 = ?, subcategoria = ? WHERE id = ?', (nova_categoria, nova_subcategoria, id_lancamento))
    else:
        cursor.execute('UPDATE lancamentos SET categoria_503020 = ? WHERE id = ?', (nova_categoria, id_lancamento))
    conn.commit()
    conn.close()

def atualizar_categorias_lote(lista_alteracoes):
    """lista_alteracoes: lista de tuplas (nova_categoria, id_lancamento) ou (nova_categoria, nova_subcategoria, id_lancamento) ou (nova_categoria, nova_subcategoria, novo_status, id_lancamento)"""
    if not lista_alteracoes:
        return
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    if len(lista_alteracoes[0]) == 4:
        cursor.executemany('UPDATE lancamentos SET categoria_503020 = ?, subcategoria = ?, status = ? WHERE id = ?', lista_alteracoes)
    elif len(lista_alteracoes[0]) == 3:
        cursor.executemany('UPDATE lancamentos SET categoria_503020 = ?, subcategoria = ? WHERE id = ?', lista_alteracoes)
    else:
        cursor.executemany('UPDATE lancamentos SET categoria_503020 = ? WHERE id = ?', lista_alteracoes)
    conn.commit()
    conn.close()

def atualizar_status_lote(lista_ids, novo_status="Pago"):
    if not lista_ids:
        return
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    placeholders = ','.join(['?'] * len(lista_ids))
    cursor.execute(f"UPDATE lancamentos SET status = ? WHERE id IN ({placeholders})", tuple([novo_status] + list(lista_ids)))
    conn.commit()
    conn.close()

def listar_metas_categorias():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT subcategoria, limite_mensal FROM metas_categorias")
    rows = dict(cursor.fetchall())
    conn.close()
    return rows

def salvar_meta_categoria(subcategoria, limite_mensal):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    if float(limite_mensal) <= 0:
        cursor.execute("DELETE FROM metas_categorias WHERE subcategoria = ?", (subcategoria,))
    else:
        cursor.execute("INSERT OR REPLACE INTO metas_categorias (subcategoria, limite_mensal) VALUES (?, ?)", (subcategoria, float(limite_mensal)))
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
try:
    sincronizar_subcategorias_existentes()
except Exception:
    pass

