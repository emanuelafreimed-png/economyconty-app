import re
import uuid
from dateutil.relativedelta import relativedelta
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, date, timedelta
import database
from pdf_extractor import extrair_dados_santander
from utils import render_footer_economyconty, obter_cor_banco

def render_faturas(user_id, nome_usuario="", manu_face_b64=""):
    def listar_lancamentos():
        return database.listar_lancamentos(user_id)
    def inserir_lancamento(tipo, descricao, valor, data_vencimento, categoria="Geral", conta="Conta Principal", status="Realizado", protocolo=None, data_pagamento=None, tributavel=0, dedutivel=0, **kwargs):
        return database.inserir_lancamento(user_id, tipo, descricao, valor, data_vencimento, categoria=categoria, conta=conta, status=status, protocolo=protocolo, data_pagamento=data_pagamento, tributavel=tributavel, dedutivel=dedutivel, **kwargs)

    st.markdown("""
    <div style="margin-bottom: 1.5rem; padding-bottom: 0.8rem; border-bottom: 1px solid rgba(212, 175, 55, 0.2);">
        <h1 style="margin: 0; font-size: 2rem; font-weight: 800; background: linear-gradient(90deg, #F9FAFB, #D4AF37); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
            💳 Gestão de Faturas de Cartão
        </h1>
        <p style="margin: 4px 0 0 0; color: #9CA3AF; font-size: 0.9rem;">Leitura de faturas (Itaú, Santander, Nubank), cálculo do melhor dia de compra e projeção de parcelas</p>
    </div>
    """, unsafe_allow_html=True)
    
    # --- PAINEL ANALÍTICO: EVOLUÇÃO DAS FATURAS ---
    st.write("### 📊 Evolução Mensal dos Gastos com Cartão")
    df_todos_lanc = listar_lancamentos()
    df_cartao_evol = pd.DataFrame()
    
    if not df_todos_lanc.empty:
        df_cartao_evol = df_todos_lanc[df_todos_lanc['banco'].str.contains('Cartão|Cartao', case=False, na=False)].copy()
        
    if not df_cartao_evol.empty:
        df_cartao_evol['valor'] = pd.to_numeric(df_cartao_evol['valor'], errors='coerce').fillna(0.0)
        df_cartao_evol['data_ref'] = pd.to_datetime(df_cartao_evol['data_pagamento'])
        df_cartao_evol['ano_mes'] = df_cartao_evol['data_ref'].dt.strftime('%Y-%m')
        df_cartao_evol['mes_ano'] = df_cartao_evol['data_ref'].dt.strftime('%m/%Y')
        df_cartao_evol = df_cartao_evol.sort_values('ano_mes')
        
        # Totais consolidados por mês
        totais_por_mes = df_cartao_evol.groupby(['ano_mes', 'mes_ano'])['valor'].sum().reset_index()
        total_acumulado = df_cartao_evol['valor'].sum()
        media_mensal = totais_por_mes['valor'].mean() if not totais_por_mes.empty else 0.0
        maior_fatura_row = totais_por_mes.loc[totais_por_mes['valor'].idxmax()] if not totais_por_mes.empty else None
        fatura_recente_row = totais_por_mes.iloc[-1] if not totais_por_mes.empty else None
        
        # Métricas de resumo
        m_col1, m_col2, m_col3, m_col4 = st.columns(4)
        if fatura_recente_row is not None:
            val_rec_fmt = f"R$ {fatura_recente_row['valor']:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            m_col1.metric("Última Fatura", val_rec_fmt, delta=f"Ref: {fatura_recente_row['mes_ano']}", delta_color="off")
        m_col2.metric("Média Mensal", f"R$ {media_mensal:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        if maior_fatura_row is not None:
            val_max_fmt = f"R$ {maior_fatura_row['valor']:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            m_col3.metric("Maior Fatura", val_max_fmt, delta=f"Pico: {maior_fatura_row['mes_ano']}", delta_color="off")
        m_col4.metric("Total Acumulado", f"R$ {total_acumulado:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        
        st.write("")
        
        # --- DOIS GRÁFICOS DE EVOLUÇÃO ---
        g_col1, g_col2 = st.columns(2)
        
        with g_col1:
            tab_bar, tab_lin = st.tabs(["💳 Por Cartão (Comparativo)", "📈 Linha de Tendência Total"])
            
            with tab_bar:
                df_mes_cartao = df_cartao_evol.groupby(['ano_mes', 'mes_ano', 'banco'])['valor'].sum().reset_index()
                mapa_cores_cartao = {b: obter_cor_banco(b) for b in df_mes_cartao['banco'].unique()}
                fig1 = px.bar(
                    df_mes_cartao,
                    x='mes_ano',
                    y='valor',
                    color='banco',
                    barmode='group',
                    title='Total de Gastos por Cartão / Mês',
                    color_discrete_map=mapa_cores_cartao
                )
                fig1.update_traces(texttemplate='R$ %{y:,.2f}', textposition='outside', opacity=0.88, marker=dict(line=dict(width=1, color='rgba(255,255,255,0.08)')))
                fig1.update_layout(
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    font=dict(family='Plus Jakarta Sans', color='#F9FAFB'),
                    xaxis=dict(title='Mês da Fatura', showgrid=False),
                    yaxis=dict(title='Valor Total (R$)', gridcolor='rgba(212, 175, 55, 0.1)'),
                    legend=dict(orientation='h', yanchor='bottom', y=-0.35, xanchor='center', x=0.5)
                )
                st.plotly_chart(fig1, use_container_width=True)
                
            with tab_lin:
                fig_linha = px.line(
                    totais_por_mes,
                    x='mes_ano',
                    y='valor',
                    markers=True,
                    title='Evolução Histórica do Total das Faturas',
                    color_discrete_sequence=['#C5A556']
                )
                fig_linha.update_traces(
                    line=dict(width=2.5, color='#C5A556'), 
                    marker=dict(size=8, color='#D97736', line=dict(width=1.5, color='#E2D3A8')), 
                    texttemplate='R$ %{y:,.2f}', 
                    textposition='top center'
                )
                fig_linha.update_layout(
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    font=dict(family='Plus Jakarta Sans', color='#F9FAFB'),
                    xaxis=dict(title='Mês da Fatura', showgrid=False),
                    yaxis=dict(title='Valor Total (R$)', gridcolor='rgba(212, 175, 55, 0.1)')
                )
                st.plotly_chart(fig_linha, use_container_width=True)
                
        with g_col2:
            tab_cat, tab_pct = st.tabs(["🎯 Por Categoria (50/30/20)", "📊 Distribuição Percentual"])
            
            cores_cat = {
                'Necessidade (50%)': '#4E89AE',   # Azul Ardósia Suave
                'Desejo (30%)': '#D97736',        # Âmbar / Terracota Suave
                'Investimento (20%)': '#42986E',   # Verde Sálvia / Esmeralda Suave
                'Renda (Não se aplica)': '#8E9AA8' # Cinza Neutro Suave
            }
            df_mes_cat = df_cartao_evol.groupby(['ano_mes', 'mes_ano', 'categoria_503020'])['valor'].sum().reset_index()
            
            with tab_cat:
                fig2 = px.bar(
                    df_mes_cat,
                    x='mes_ano',
                    y='valor',
                    color='categoria_503020',
                    barmode='stack',
                    title='Composição das Faturas por Categoria',
                    color_discrete_map=cores_cat
                )
                fig2.update_traces(texttemplate='R$ %{y:,.2f}', textposition='inside', opacity=0.88, marker=dict(line=dict(width=1, color='rgba(255,255,255,0.08)')))
                fig2.update_layout(
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    font=dict(family='Plus Jakarta Sans', color='#F9FAFB'),
                    xaxis=dict(title='Mês da Fatura', showgrid=False),
                    yaxis=dict(title='Valor (R$)', gridcolor='rgba(212, 175, 55, 0.1)'),
                    legend=dict(orientation='h', yanchor='bottom', y=-0.35, xanchor='center', x=0.5)
                )
                st.plotly_chart(fig2, use_container_width=True)
                
            with tab_pct:
                fig_pct = px.bar(
                    df_mes_cat,
                    x='mes_ano',
                    y='valor',
                    color='categoria_503020',
                    barmode='relative',
                    title='Percentual de Necessidades vs Desejos',
                    color_discrete_map=cores_cat
                )
                fig_pct.update_traces(opacity=0.88, marker=dict(line=dict(width=1, color='rgba(255,255,255,0.08)')))
                fig_pct.update_layout(
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    font=dict(family='Plus Jakarta Sans', color='#F9FAFB'),
                    xaxis=dict(title='Mês da Fatura', showgrid=False),
                    yaxis=dict(title='Proporção', gridcolor='rgba(212, 175, 55, 0.1)'),
                    legend=dict(orientation='h', yanchor='bottom', y=-0.35, xanchor='center', x=0.5)
                )
                st.plotly_chart(fig_pct, use_container_width=True)
                
        st.markdown("---")
    else:
        st.info("💡 Nenhuma fatura de cartão de crédito registrada ainda. Faça o upload abaixo para gerar a análise gráfica automaticamente!")
        st.markdown("---")
        
    # 1. Calculadora de Melhor Dia de Compra
    with st.expander("📅 Descobrir Melhor Dia para Comprar", expanded=False):
        st.write("Digite o dia de vencimento da sua fatura para saber quando é o melhor dia para comprar (quando a fatura fecha e você ganha mais de 30 dias para pagar).")
        dia_vencimento = st.number_input("Dia do Vencimento do Cartão", min_value=1, max_value=31, value=10)
        
        # Geralmente a fatura fecha 7 a 9 dias antes do vencimento. Usaremos 8 dias como média de mercado.
        dia_fechamento = dia_vencimento - 8
        if dia_fechamento <= 0:
            dia_fechamento += 30 # Ajuste para o mês anterior
            
        st.success(f"**O seu Melhor Dia de Compra é dia {dia_fechamento}!** Comprando neste dia, a cobrança só virá na fatura do mês seguinte.")

    st.markdown("---")
    st.write("Faça o upload das suas faturas! Aceitamos **Excel (Itaú, Nubank)** e **PDF (Santander)**.")
    
    arquivos_fatura = st.file_uploader("Arraste os arquivos da fatura aqui", type=["xlsx", "xls", "pdf"], accept_multiple_files=True)
    
    if arquivos_fatura:
        for arquivo in arquivos_fatura:
            try:
                # Verifica se é Santander (PDF)
                if arquivo.name.lower().endswith(".pdf"):
                    st.write(f"### 🧾 Fatura Santander: {arquivo.name}")
                    
                    cache_key_sant = f"df_sant_{arquivo.name}_{arquivo.size}"
                    if cache_key_sant not in st.session_state:
                        if hasattr(arquivo, 'seek'):
                            arquivo.seek(0)
                        dados_santander = extrair_dados_santander(arquivo)
                        if not dados_santander:
                            st.warning(f"Não conseguimos ler despesas no arquivo {arquivo.name}. É uma fatura do Santander válida?")
                            continue
                            
                        # Prepara a tabela do editor
                        for d in dados_santander:
                            d['Categoria'] = "Desejo (30%)"
                            if "microsoft" in d['Descrição'].lower() or "youse" in d['Descrição'].lower():
                                d['Categoria'] = "Necessidade (50%)"
                                
                        st.session_state[cache_key_sant] = pd.DataFrame(dados_santander)
                    
                    df_editor = st.session_state[cache_key_sant]
                    soma_total = df_editor[df_editor['Tipo'] == 'Despesa']['Valor'].sum() - df_editor[df_editor['Tipo'] == 'Receita']['Valor'].sum() if 'Tipo' in df_editor.columns else df_editor['Valor'].sum()
                    st.markdown(f"**Total Identificado:** `R$ {soma_total:,.2f}`".replace(",", "X").replace(".", ",").replace("X", "."))
                    
                    config_colunas = {
                        "Categoria": st.column_config.SelectboxColumn("Categoria", options=["Necessidade (50%)", "Desejo (30%)", "Investimento (20%)", "Renda (Não se aplica)"], required=True),
                        "Tipo": st.column_config.SelectboxColumn("Tipo", options=["Despesa", "Receita"], required=True),
                        "Valor": st.column_config.NumberColumn("Valor (R$)", format="R$ %.2f", disabled=True),
                        "Data": st.column_config.TextColumn("Data", disabled=True),
                        "Parcela": st.column_config.TextColumn("Parcela", disabled=True),
                        "Descrição": st.column_config.TextColumn("Descrição (Editável)")
                    }
                    
                    df_final = st.data_editor(df_editor, column_config=config_colunas, width="stretch", hide_index=True, key=f"editor_santander_{arquivo.name}")
                    
                    projetar_parcelas = st.checkbox("Projetar parcelas futuras automaticamente? (Cuidado com faturas antigas repetidas)", value=False, key=f"chk_proj_santander_{arquivo.name}")
                    data_pagamento_fatura = st.date_input("Qual é a data real de pagamento/vencimento desta fatura?", key=f"data_pgto_sant_{arquivo.name}")
                    
                    if st.button("💳 Salvar Fatura Santander", type="primary", key=f"btn_salvar_santander_{arquivo.name}"):
                        protocolo = str(uuid.uuid4())[:8].upper()
                        
                        banco_cartao = "Cartão Santander"
                        for idx, row_f in df_final.iterrows():
                            tipo = row_f['Tipo']
                            desc = row_f['Descrição']
                            cat = row_f['Categoria']
                            valor = float(row_f['Valor'])
                            data_str_curta = row_f['Data'] # Vem como 05/12
                            parcela_txt = row_f['Parcela']
                            
                            # Transforma '05/12' em data real. Assumimos o ano atual, mas você pode editar lá.
                            # Para simplificar na inserção, criamos '2026-12-05'
                            ano_atual = pd.Timestamp.now().year
                            dia_s, mes_s = data_str_curta.split('/')
                            data_venc_str = f"{ano_atual}-{mes_s}-{dia_s}"
                            
                            inserir_lancamento(tipo, desc, valor, data_venc_str, cat, banco_cartao, "Pago", protocolo, str(data_pagamento_fatura))
                            
                            if projetar_parcelas and parcela_txt != "-":
                                try:
                                    atual, total = map(int, parcela_txt.split('/'))
                                    if atual < total:
                                        data_obj = pd.to_datetime(data_venc_str)
                                        for p in range(atual + 1, total + 1):
                                            data_futura = data_obj + relativedelta(months=p - atual)
                                            desc_futura = f"{desc} (Parcela {p}/{total})"
                                            inserir_lancamento(tipo, desc_futura, valor, data_futura.strftime('%Y-%m-%d'), cat, banco_cartao, "A Pagar", protocolo, data_futura.strftime('%Y-%m-%d'))
                                except Exception as e:
                                    st.error(f"Erro ao projetar parcela de {desc}: {e}")
                                    
                        st.success(f"Fatura Santander '{arquivo.name}' importada e gravada com sucesso!")
                        if cache_key_sant in st.session_state:
                            del st.session_state[cache_key_sant]
                    st.markdown("---")
                    continue
                    
                # Lógica original de Excel (Itaú)
                cache_key_excel = f"df_excel_{arquivo.name}_{arquivo.size}"
                if cache_key_excel not in st.session_state:
                    if hasattr(arquivo, 'seek'):
                        arquivo.seek(0)
                    # Lê o excel inteiro de uma vez (evita problemas de fechar o arquivo na memória)
                    df_raw = pd.read_excel(arquivo, header=None)
                    
                    # Procura qual linha tem a palavra 'Data' e 'Valor' juntas
                    linha_cabecalho = None
                    for idx, row in df_raw.iterrows():
                        row_str = row.astype(str).str.lower()
                        if row_str.str.contains('data').any() and row_str.str.contains('valor').any():
                            linha_cabecalho = idx
                            break
                            
                    if linha_cabecalho is None:
                        st.warning(f"Não encontramos a coluna de 'Data' e 'Valor' no arquivo {arquivo.name}. O formato pode ser diferente.")
                        continue
                        
                    # Recorta o dataframe da linha seguinte ao cabeçalho em diante
                    df_fatura = df_raw.iloc[linha_cabecalho + 1:].copy()
                    
                    # Nomeia as colunas de acordo com o cabeçalho encontrado
                    df_fatura.columns = df_raw.iloc[linha_cabecalho].values
                    
                    # Identifica as colunas usando os nomes reais do arquivo
                    cols_data = [c for c in df_fatura.columns if 'data' in str(c).lower()]
                    cols_desc = [c for c in df_fatura.columns if 'lançamento' in str(c).lower() or 'descri' in str(c).lower()]
                    cols_valor = [c for c in df_fatura.columns if 'valor' in str(c).lower()]
                    
                    if not cols_data or not cols_desc or not cols_valor:
                        st.warning(f"Não conseguimos mapear as colunas de Data/Descrição/Valor na fatura {arquivo.name}.")
                        continue
                        
                    col_data = cols_data[0]
                    col_desc = cols_desc[0]
                    col_valor = cols_valor[0]
                    
                    # Filtra apenas o que é gasto válido
                    df_fatura = df_fatura[df_fatura[col_valor].notna()]
                    df_fatura = df_fatura[df_fatura[col_valor] != 'Valor']
                    df_fatura = df_fatura[~df_fatura[col_desc].astype(str).str.contains("Pagamento", case=False, na=False)] # Ignora pagamentos de fatura
                    
                    despesas_fatura = []
                    for index, row in df_fatura.iterrows():
                        # Corrige a leitura do valor mantendo as casas decimais se for float
                        val_raw = row[col_valor]
                        if pd.isna(val_raw):
                            continue
                            
                        if isinstance(val_raw, (int, float)):
                            val_num = float(val_raw)
                        else:
                            val_num = pd.to_numeric(str(val_raw).replace('.', '').replace(',', '.'), errors='coerce')
                            
                        if pd.isna(val_num) or val_num == 0:
                            continue
                            
                        # Tenta achar info de parcela na linha toda
                        row_str = str(row.tolist())
                        match_parcela = re.search(r'Parcela\s+(\d+)\s+de\s+(\d+)', row_str, re.IGNORECASE)
                        info_parcela = f"{match_parcela.group(1)}/{match_parcela.group(2)}" if match_parcela else "-"
                        
                        data_str = str(row[col_data]).split(' ')[0]
                        tipo_sugerido = "Despesa" if val_num > 0 else "Receita"
                        
                        desc_str = str(row[col_desc])
                        cat_sugerida = "Desejo (30%)"
                        
                        # Regras de auto-categorização personalizadas
                        if "microsoft" in desc_str.lower() or "youse" in desc_str.lower():
                            cat_sugerida = "Necessidade (50%)"
                        elif tipo_sugerido == "Receita" or "cancelamento" in desc_str.lower() or "estorno" in desc_str.lower():
                            cat_sugerida = "Renda (Não se aplica)"
                        
                        despesas_fatura.append({
                            "Data": data_str,
                            "Descrição": desc_str,
                            "Parcela": info_parcela,
                            "Valor": abs(val_num),
                            "Categoria": cat_sugerida,
                            "Tipo": tipo_sugerido
                        })
                    
                    if len(despesas_fatura) > 0:
                        st.session_state[cache_key_excel] = pd.DataFrame(despesas_fatura)
                    else:
                        st.session_state[cache_key_excel] = pd.DataFrame()

                df_editor = st.session_state.get(cache_key_excel)
                if df_editor is not None and len(df_editor) > 0:
                    st.write(f"### 🧾 Arquivo: {arquivo.name} ({len(df_editor)} despesas)")
                    soma_total = df_editor[df_editor['Tipo'] == 'Despesa']['Valor'].sum() - df_editor[df_editor['Tipo'] == 'Receita']['Valor'].sum() if 'Tipo' in df_editor.columns else df_editor['Valor'].sum()
                    
                    st.markdown(f"**Total Identificado:** `R$ {soma_total:,.2f}`".replace(",", "X").replace(".", ",").replace("X", "."))
                    
                    # Cria a visualização estilo fatura interativa
                    config_colunas = {
                        "Categoria": st.column_config.SelectboxColumn("Categoria", options=["Necessidade (50%)", "Desejo (30%)", "Investimento (20%)", "Renda (Não se aplica)"], required=True),
                        "Tipo": st.column_config.SelectboxColumn("Tipo", options=["Despesa", "Receita"], required=True),
                        "Valor": st.column_config.NumberColumn("Valor (R$)", format="R$ %.2f", disabled=True),
                        "Data": st.column_config.TextColumn("Data", disabled=True),
                        "Parcela": st.column_config.TextColumn("Parcela", disabled=True),
                        "Descrição": st.column_config.TextColumn("Descrição (Editável)")
                    }
                    
                    df_final = st.data_editor(df_editor, column_config=config_colunas, width="stretch", hide_index=True, key=f"editor_{arquivo.name}")
                    
                    projetar_parcelas = st.checkbox("Projetar parcelas futuras automaticamente? (Cuidado com faturas antigas repetidas)", value=False, key=f"chk_proj_{arquivo.name}")
                    data_pagamento_fatura = st.date_input("Qual é a data real de pagamento/vencimento desta fatura?", key=f"data_pgto_{arquivo.name}")
                    
                    if st.button("💳 Salvar Fatura no Banco de Dados", type="primary", key=f"btn_salvar_{arquivo.name}"):
                        protocolo = str(uuid.uuid4())[:8].upper()
                        
                        banco_cartao = "Cartão Itaú"
                        for idx, row_f in df_final.iterrows():
                            tipo = row_f['Tipo']
                            desc = row_f['Descrição']
                            cat = row_f['Categoria']
                            valor = float(row_f['Valor']) # Força o tipo float nativo do Python!
                            data_venc_str = row_f['Data']
                            parcela_txt = row_f['Parcela']
                            
                            # Salva a parcela atual
                            inserir_lancamento(tipo, desc, valor, data_venc_str, cat, banco_cartao, "Pago", protocolo, str(data_pagamento_fatura))
                            
                            # Projeta as futuras se tiver parcela ex: 1/4
                            if projetar_parcelas and parcela_txt != "-":
                                try:
                                    atual, total = map(int, parcela_txt.split('/'))
                                    if atual < total:
                                        data_obj = pd.to_datetime(data_venc_str)
                                        for p in range(atual + 1, total + 1):
                                            data_futura = data_obj + relativedelta(months=p - atual)
                                            desc_futura = f"{desc} (Parcela {p}/{total})"
                                            inserir_lancamento(tipo, desc_futura, valor, data_futura.strftime('%Y-%m-%d'), cat, banco_cartao, "A Pagar", protocolo, data_futura.strftime('%Y-%m-%d'))
                                except Exception as e:
                                    st.error(f"Erro ao projetar parcela de {desc}: {e}")
                                    
                        st.success(f"Fatura '{arquivo.name}' importada e gravada com sucesso!")
                        if cache_key_excel in st.session_state:
                            del st.session_state[cache_key_excel]
                else:
                    st.info("Nenhuma despesa válida encontrada.")
                
                st.markdown("---")
            
            except Exception as e:
                st.error(f"Erro ao ler a fatura {arquivo.name}: {e}")

