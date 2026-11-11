import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, date
import database
from utils import render_footer_economyconty, obter_cor_banco

def render_extrato(user_id, nome_usuario="", manu_face_b64=""):
    def listar_lancamentos():
        return database.listar_lancamentos(user_id)
    def excluir_lancamento(id_lancamento):
        return database.excluir_lancamento(user_id, id_lancamento)
    def excluir_lancamento_protocolo(protocolo):
        return database.excluir_lancamento_protocolo(user_id, protocolo)
    def excluir_lancamentos_multiplos(lista_ids):
        return database.excluir_lancamentos_multiplos(user_id, lista_ids)
    def atualizar_categoria_lancamento(id_lancamento, nova_categoria, nova_subcategoria=None):
        return database.atualizar_categoria_lancamento(user_id, id_lancamento, nova_categoria, nova_subcategoria=nova_subcategoria)
    def atualizar_categorias_lote(lista_alteracoes):
        return database.atualizar_categorias_lote(user_id, lista_alteracoes)
    def atualizar_status_lote(lista_ids, novo_status="Pago"):
        return database.atualizar_status_lote(user_id, lista_ids, novo_status=novo_status)
    TODAS_SUBCATEGORIAS = database.TODAS_SUBCATEGORIAS
    MAPA_SUBCATEGORIA_503020 = database.MAPA_SUBCATEGORIA_503020

    st.markdown("""
    <div style="margin-bottom: 1.5rem; padding-bottom: 0.8rem; border-bottom: 1px solid rgba(212, 175, 55, 0.2);">
        <h1 style="margin: 0; font-size: 2rem; font-weight: 800; background: linear-gradient(90deg, #F9FAFB, #D4AF37); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
            📊 Extrato Consolidado & Alertas
        </h1>
        <p style="margin: 4px 0 0 0; color: #9CA3AF; font-size: 0.9rem;">Acompanhe o status dos pagamentos com filtro por período, busca rápida e alertas visuais de vencimento</p>
    </div>
    """, unsafe_allow_html=True)
    df = listar_lancamentos()
    
    if not df.empty:
        # Prepara campos de data e valor para cálculos
        df['data_vencimento_dt'] = pd.to_datetime(df['data_vencimento'], errors='coerce').dt.date
        df['data_pagamento_dt'] = pd.to_datetime(df['data_pagamento'], errors='coerce').dt.date
        df['valor'] = pd.to_numeric(df['valor'], errors='coerce').fillna(0.0)
        hoje = pd.Timestamp.now().date()
        
        # Datas de referência
        datas_validas = df['data_pagamento_dt'].dropna()
        if datas_validas.empty:
            datas_validas = df['data_vencimento_dt'].dropna()
            
        data_min_global = datas_validas.min() if not datas_validas.empty else hoje
        data_max_global = datas_validas.max() if not datas_validas.empty else hoje
        
        primeiro_dia_mes = hoje.replace(day=1)
        ultimo_dia_mes = (pd.Timestamp(hoje.year, hoje.month, 1) + pd.offsets.MonthEnd(1)).date()
        
        primeiro_dia_mes_ant = (primeiro_dia_mes - pd.Timedelta(days=1)).replace(day=1)
        ultimo_dia_mes_ant = primeiro_dia_mes - pd.Timedelta(days=1)
        
        primeiro_dia_ano = pd.to_datetime(f"{hoje.year}-01-01").date()
        ultimo_dia_ano = pd.to_datetime(f"{hoje.year}-12-31").date()
        
        # --- PAINEL DE FILTRAGEM POR DATA ---
        st.markdown("""
        <div style="background: rgba(16, 28, 45, 0.65); border: 1px solid rgba(212, 175, 55, 0.25); border-radius: 12px; padding: 14px 18px 12px 18px; margin-bottom: 20px;">
            <div style="font-size: 0.82rem; font-weight: 700; color: #D4AF37; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 8px;">
                🗓️ Filtro de Período & Detalhes
            </div>
        """, unsafe_allow_html=True)
        
        f_col1, f_col2, f_col3 = st.columns([1.2, 1.4, 1.8], vertical_alignment="bottom")
        with f_col1:
            campo_base = st.selectbox(
                "Filtrar por qual Data:",
                ["Data do Pagamento", "Data de Vencimento/Compra"],
                index=0,
                key="filtro_extrato_base"
            )
            
        with f_col2:
            preset_opcao = st.selectbox(
                "📅 Seleção de Período:",
                [
                    "Mês Atual",
                    "Mês Anterior",
                    "Últimos 30 Dias",
                    "Últimos 90 Dias",
                    "Ano Atual (2026)",
                    "Personalizado (Calendário)",
                    "Todo o Histórico"
                ],
                index=0,
                key="filtro_extrato_preset"
            )
            
        with f_col3:
            if preset_opcao == "Mês Atual":
                dt_inicio = primeiro_dia_mes
                dt_fim = ultimo_dia_mes
                st.caption(f"📅 Período ativo: **{dt_inicio.strftime('%d/%m/%Y')}** até **{dt_fim.strftime('%d/%m/%Y')}**")
            elif preset_opcao == "Mês Anterior":
                dt_inicio = primeiro_dia_mes_ant
                dt_fim = ultimo_dia_mes_ant
                st.caption(f"📅 Período ativo: **{dt_inicio.strftime('%d/%m/%Y')}** até **{dt_fim.strftime('%d/%m/%Y')}**")
            elif preset_opcao == "Últimos 30 Dias":
                dt_inicio = hoje - pd.Timedelta(days=30)
                dt_fim = hoje
                st.caption(f"📅 Período ativo: **{dt_inicio.strftime('%d/%m/%Y')}** até **{dt_fim.strftime('%d/%m/%Y')}**")
            elif preset_opcao == "Últimos 90 Dias":
                dt_inicio = hoje - pd.Timedelta(days=90)
                dt_fim = hoje
                st.caption(f"📅 Período ativo: **{dt_inicio.strftime('%d/%m/%Y')}** até **{dt_fim.strftime('%d/%m/%Y')}**")
            elif preset_opcao == "Ano Atual (2026)":
                dt_inicio = primeiro_dia_ano
                dt_fim = ultimo_dia_ano
                st.caption(f"📅 Período ativo: **{dt_inicio.strftime('%d/%m/%Y')}** até **{dt_fim.strftime('%d/%m/%Y')}**")
            elif preset_opcao == "Todo o Histórico":
                dt_inicio = data_min_global
                dt_fim = data_max_global
                st.caption(f"📅 Período ativo: **{dt_inicio.strftime('%d/%m/%Y')}** até **{dt_fim.strftime('%d/%m/%Y')}** (Histórico Completo)")
            else: # Personalizado
                range_picker = st.date_input(
                    "Selecione Início e Fim:",
                    value=(primeiro_dia_mes, hoje),
                    format="DD/MM/YYYY",
                    key="filtro_extrato_custom_range"
                )
                if isinstance(range_picker, (tuple, list)) and len(range_picker) == 2:
                    dt_inicio, dt_fim = range_picker
                elif isinstance(range_picker, (tuple, list)) and len(range_picker) == 1:
                    dt_inicio, dt_fim = range_picker[0], range_picker[0]
                else:
                    dt_inicio, dt_fim = primeiro_dia_mes, hoje
                    
        f_sub1, f_sub2, f_sub3, f_sub4 = st.columns([0.9, 1.0, 1.3, 1.4], vertical_alignment="bottom")
        with f_sub1:
            filtro_status = st.selectbox("Status:", ["Todos", "Pago", "Pendente"], index=0, key="filtro_extrato_status")
        with f_sub2:
            filtro_tipo = st.selectbox("Tipo:", ["Todos", "Despesa", "Receita", "Outras Receitas", "Resgate de Investimento"], index=0, key="filtro_extrato_tipo")
        with f_sub3:
            opcoes_filtro_sub = ["Todas as Categorias"] + sorted(list(df['subcategoria'].dropna().unique())) if 'subcategoria' in df.columns else ["Todas as Categorias"]
            filtro_subcat = st.selectbox("🏷️ Categoria (Ícone):", opcoes_filtro_sub, index=0, key="filtro_extrato_subcat")
        with f_sub4:
            filtro_busca = st.text_input("🔍 Busca por texto:", placeholder="Descrição, categoria ou banco...", key="filtro_extrato_busca")
            
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Aplicar filtros
        col_data_alvo = 'data_pagamento_dt' if campo_base == "Data do Pagamento" else 'data_vencimento_dt'
        datas_filtro = df[col_data_alvo].fillna(df['data_vencimento_dt'])
        mask_data = (datas_filtro >= dt_inicio) & (datas_filtro <= dt_fim)
        
        df_filtrado = df[mask_data].copy()
        
        if filtro_status != "Todos":
            df_filtrado = df_filtrado[df_filtrado['status'] == filtro_status]
            
        if filtro_tipo != "Todos":
            df_filtrado = df_filtrado[df_filtrado['tipo'] == filtro_tipo]

        if filtro_subcat != "Todas as Categorias" and 'subcategoria' in df_filtrado.columns:
            df_filtrado = df_filtrado[df_filtrado['subcategoria'] == filtro_subcat]
            
        if filtro_busca:
            termo = filtro_busca.lower()
            mask_busca = (
                df_filtrado['descricao'].astype(str).str.lower().str.contains(termo, na=False) |
                df_filtrado['categoria_503020'].astype(str).str.lower().str.contains(termo, na=False) |
                df_filtrado['subcategoria'].astype(str).str.lower().str.contains(termo, na=False) |
                df_filtrado['banco'].astype(str).str.lower().str.contains(termo, na=False)
            )
            df_filtrado = df_filtrado[mask_busca]
            
        # Métricas resumidas do período filtrado
        total_rec = df_filtrado[df_filtrado['tipo'].isin(['Receita', 'Outras Receitas', 'Resgate de Investimento'])]['valor'].sum()
        total_desp = df_filtrado[df_filtrado['tipo'] == 'Despesa']['valor'].sum()
        saldo_periodo = total_rec - total_desp
        pendentes_qtd = len(df_filtrado[df_filtrado['status'] == 'Pendente'])
        
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("📥 Entradas do Período", f"R$ {total_rec:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        m2.metric("📤 Saídas do Período", f"R$ {total_desp:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        m3.metric(
            "💰 Saldo do Período", 
            f"R$ {saldo_periodo:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
            delta=f"R$ {saldo_periodo:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") if saldo_periodo != 0 else None,
            delta_color="normal" if saldo_periodo >= 0 else "inverse"
        )
        m4.metric("📊 Lançamentos", f"{len(df_filtrado)} itens", delta=f"{pendentes_qtd} pendente(s)" if pendentes_qtd > 0 else "Nenhum pendente", delta_color="off" if pendentes_qtd == 0 else "inverse")
        
        st.write("")
        
        # Função que define as regras de cores da tabela
        def aplicar_cores(row):
            try:
                if pd.notna(row.get('Data da Compra')) and row.get('Data da Compra') != '':
                    data_ref = pd.to_datetime(row['Data da Compra'], format='%d/%m/%Y').date()
                else:
                    data_ref = pd.to_datetime(row['Data do Pgto.'], format='%d/%m/%Y').date()
            except:
                data_ref = hoje
                
            if row['Status'] == 'Pago':
                return ['background-color: rgba(16, 185, 129, 0.18); color: #34D399; font-weight: 600;'] * len(row) 
            elif row['Status'] == 'Pendente':
                if data_ref < hoje:
                    return ['background-color: rgba(239, 68, 68, 0.22); color: #F87171; font-weight: 700;'] * len(row) 
                elif (data_ref - hoje).days <= 3:
                    return ['background-color: rgba(245, 158, 11, 0.22); color: #FBBF24; font-weight: 700;'] * len(row) 
            return [''] * len(row)
            
        if df_filtrado.empty:
            st.info(f"Nenhum lançamento encontrado para os filtros selecionados no período de **{dt_inicio.strftime('%d/%m/%Y')}** até **{dt_fim.strftime('%d/%m/%Y')}**.")
        else:
            # Opções de visualização da tabela
            top_t_col1, top_t_col2 = st.columns([2.6, 1.4], vertical_alignment="center")
            with top_t_col1:
                modo_tabela = st.radio(
                    "Visualização da Tabela:",
                    ["✏️ Tabela Editável (Reclassificar Categorias)", "🎨 Tabela Colorida (Alertas de Vencimento)"],
                    horizontal=True,
                    key="modo_tabela_extrato"
                )
            with top_t_col2:
                st.caption("💡 Dê 2 cliques na coluna **Categoria** para alterar e salve no botão abaixo.")

            # Preparação dos dados para exibição
            df_display = df_filtrado.copy()
            df_display = df_display.drop(columns=['protocolo', 'data_vencimento_dt', 'data_pagamento_dt'], errors='ignore')
            
            # Formata os valores monetários
            df_display['valor_formatado'] = df_display['valor'].apply(lambda x: f"R$ {float(x):,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
            
            # Formata as datas para o padrão brasileiro
            df_display['data_vencimento_fmt'] = pd.to_datetime(df_display['data_vencimento']).dt.strftime('%d/%m/%Y')
            df_display['data_pagamento_fmt'] = pd.to_datetime(df_display['data_pagamento']).dt.strftime('%d/%m/%Y') if 'data_pagamento' in df_display.columns else df_display['data_vencimento_fmt']
            
            # DataFrame para tabela colorida
            df_colorida = pd.DataFrame({
                'Tipo': df_display['tipo'],
                'Descrição': df_display['descricao'],
                'Valor': df_display['valor_formatado'],
                'Data da Compra': df_display['data_vencimento_fmt'],
                'Subcategoria': df_display['subcategoria'],
                'Categoria': df_display['categoria_503020'],
                'Conta/Banco': df_display['banco'],
                'Status': df_display['status'],
                'Data do Pgto.': df_display['data_pagamento_fmt'],
                'tributavel': df_display.get('tributavel', 0),
                'dedutivel': df_display.get('dedutivel', 0),
            }, index=df_filtrado.index)

            if modo_tabela == "🎨 Tabela Colorida (Alertas de Vencimento)":
                tabela_colorida = df_colorida.style.apply(aplicar_cores, axis=1)
                st.dataframe(tabela_colorida, width='stretch')
            else:
                # DataFrame para edição direta
                df_editor = pd.DataFrame({
                    'id': df_filtrado['id'].values,
                    'Tipo': df_display['tipo'].values,
                    'Descrição': df_display['descricao'].values,
                    'Valor': df_display['valor_formatado'].values,
                    'Data da Compra': df_display['data_vencimento_fmt'].values,
                    'Subcategoria': df_display['subcategoria'].values,
                    'Categoria': df_display['categoria_503020'].values,
                    'Conta/Banco': df_display['banco'].values,
                    'Status': df_display['status'].values,
                    'Data do Pgto.': df_display['data_pagamento_fmt'].values,
                    'tributavel': df_display.get('tributavel', 0).values,
                    'dedutivel': df_display.get('dedutivel', 0).values,
                })

                opcoes_categorias_503020 = [
                    "Necessidade (50%)",
                    "Desejo (30%)",
                    "Investimento (20%)",
                    "Renda (Não se aplica)"
                ]

                col_config = {
                    "id": st.column_config.NumberColumn("ID", disabled=True, width="small"),
                    "Tipo": st.column_config.TextColumn("Tipo", disabled=True, width="small"),
                    "Descrição": st.column_config.TextColumn("Descrição", disabled=True, width="medium"),
                    "Valor": st.column_config.TextColumn("Valor", disabled=True, width="small"),
                    "Data da Compra": st.column_config.TextColumn("Data da Compra", disabled=True, width="small"),
                    "Subcategoria": st.column_config.SelectboxColumn(
                        "Categoria (Ícone) 🏷️",
                        help="Clique duas vezes para escolher a categoria com ícone",
                        options=TODAS_SUBCATEGORIAS,
                        required=True,
                        width="medium"
                    ),
                    "Categoria": st.column_config.SelectboxColumn(
                        "Regra 50/30/20 ✏️",
                        help="Clique duas vezes ou selecione a nova categoria 50/30/20",
                        options=opcoes_categorias_503020,
                        required=True,
                        width="medium"
                    ),
                    "Conta/Banco": st.column_config.TextColumn("Conta/Banco", disabled=True, width="small"),
                    "Status": st.column_config.SelectboxColumn(
                        "Status ✅",
                        help="Altere entre Pago e Pendente com 2 cliques",
                        options=["Pago", "Pendente", "A Pagar"],
                        required=True,
                        width="small"
                    ),
                    "Data do Pgto.": st.column_config.TextColumn("Data do Pgto.", disabled=True, width="small"),
                    "tributavel": st.column_config.NumberColumn("tributavel", disabled=True, width="small"),
                    "dedutivel": st.column_config.NumberColumn("dedutivel", disabled=True, width="small"),
                }

                df_editado = st.data_editor(
                    df_editor,
                    column_config=col_config,
                    disabled=[c for c in df_editor.columns if c not in ["Categoria", "Subcategoria", "Status"]],
                    hide_index=True,
                    width='stretch',
                    key="editor_extrato_categorias"
                )

                # Detecta alterações
                diff_mask = (df_editado['Categoria'] != df_editor['Categoria']) | (df_editado['Subcategoria'] != df_editor['Subcategoria']) | (df_editado['Status'] != df_editor['Status'])
                alteracoes_pendentes = df_editado[diff_mask]
                qtd_alt = len(alteracoes_pendentes)

                btn_col1, btn_col2 = st.columns([1.5, 3], vertical_alignment="center")
                with btn_col1:
                    if qtd_alt > 0:
                        if st.button(f"💾 Salvar Alterações ({qtd_alt} item{'s' if qtd_alt > 1 else ''})", type="primary", use_container_width=True):
                            lista_upd = []
                            for idx_r, r in alteracoes_pendentes.iterrows():
                                cat_orig = df_editor.loc[idx_r, 'Categoria']
                                sub_orig = df_editor.loc[idx_r, 'Subcategoria']
                                status_orig = df_editor.loc[idx_r, 'Status']
                                nova_sub = r['Subcategoria']
                                nova_cat = r['Categoria']
                                if nova_sub != sub_orig and nova_cat == cat_orig:
                                    nova_cat = MAPA_SUBCATEGORIA_503020.get(nova_sub, nova_cat)
                                lista_upd.append((nova_cat, nova_sub, int(r['id'])))
                                if r['Status'] != status_orig:
                                    atualizar_status_lote([int(r['id'])], r['Status'])
                            atualizar_categorias_lote(lista_upd)
                            st.success(f"🎉 {len(lista_upd)} lançamento(s) atualizado(s) com sucesso!")
                            st.rerun()
                    else:
                        st.button("💾 Salvar Alterações (Sem mudanças)", disabled=True, use_container_width=True)
                
                with btn_col2:
                    if qtd_alt > 0:
                        st.info(f"⚠️ Há **{qtd_alt}** lançamento(s) alterado(s) na tabela. Clique no botão ao lado para salvar.")
                    else:
                        st.caption("Altere **Categoria (Ícone)**, **Regra 50/30/20** ou **Status** diretamente na tabela acima e clique em salvar.")

            # Formulário rápido de reclassificação individual
            with st.expander("⚡ Reclassificar Lançamento por Formulário Rápido"):
                c_rec1, c_rec2, c_rec3, c_rec4 = st.columns([2.2, 1.4, 1.3, 1.0], vertical_alignment="bottom")
                with c_rec1:
                    opcoes_itens_rec = {
                        f"ID {r['id']} | {r['descricao']} (R$ {float(r['valor']):,.2f}) — {r.get('subcategoria', '📋 Outros')}": r['id']
                        for _, r in df_filtrado.iterrows()
                    }
                    item_rec_sel = st.selectbox("Selecione o Lançamento:", list(opcoes_itens_rec.keys()), key="sel_item_rec_form")
                with c_rec2:
                    nova_sub_form = st.selectbox(
                        "Nova Categoria (Ícone):",
                        TODAS_SUBCATEGORIAS,
                        key="nova_sub_form_sel"
                    )
                with c_rec3:
                    cat_sug_f = MAPA_SUBCATEGORIA_503020.get(nova_sub_form, "Desejo (30%)")
                    op_50 = ["Necessidade (50%)", "Desejo (30%)", "Investimento (20%)", "Renda (Não se aplica)"]
                    nova_cat_form = st.selectbox(
                        "Regra 50/30/20:",
                        op_50,
                        index=op_50.index(cat_sug_f) if cat_sug_f in op_50 else 0,
                        key="nova_cat_form_sel"
                    )
                with c_rec4:
                    if st.button("Aplicar", type="secondary", use_container_width=True, key="btn_aplica_nova_cat_form"):
                        id_rec_alvo = opcoes_itens_rec[item_rec_sel]
                        atualizar_categoria_lancamento(id_rec_alvo, nova_cat_form, nova_sub_form)
                        st.success("Categoria atualizada com sucesso!")
                        st.rerun()

            # Botão de exportação para CSV
            csv_dados = df_colorida.to_csv(index=False).encode('utf-8-sig')
            st.download_button(
                label="📥 Exportar Extrato Filtrado (CSV)",
                data=csv_dados,
                file_name=f"extrato_economyconty_{dt_inicio.strftime('%Y%m%d')}_{dt_fim.strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
            
        st.write("---")
        with st.expander("🗑️ Central de Exclusão de Lançamentos ou Lotes (Gestão Segura)", expanded=False):
            tab_ind, tab_lote, tab_multi = st.tabs([
                "🔍 Excluir Lançamento Individual (Com Raio-X)", 
                "📦 Excluir por Lote / Importação (Com Pré-Visualização)",
                "☑️ Exclusão Rápida por Seleção (Tabela)"
            ])
            
            # --- TAB 1: INDIVIDUAL ---
            with tab_ind:
                st.write("#### 🔍 Localizar e Confirmar Lançamento para Exclusão")
                st.caption("Consulte os dados completos antes de apagar para ter certeza absoluta de que é o lançamento correto.")
                
                f_ind_col1, f_ind_col2 = st.columns([2, 1.2])
                with f_ind_col1:
                    filtro_ind = st.text_input("Buscar por descrição, valor ou ID:", key="filtro_exc_ind", placeholder="Ex: Escola, Uber, 390.00...")
                with f_ind_col2:
                    bancos_disp_exc = ["Todos os Bancos"] + sorted(list(df['banco'].dropna().unique()))
                    banco_filtro_ind = st.selectbox("Filtrar por Conta/Banco:", bancos_disp_exc, key="banco_exc_ind")
                    
                df_busca_ind = df.copy()
                if banco_filtro_ind != "Todos os Bancos":
                    df_busca_ind = df_busca_ind[df_busca_ind['banco'] == banco_filtro_ind]
                if filtro_ind:
                    t_term = filtro_ind.lower()
                    df_busca_ind = df_busca_ind[
                        df_busca_ind['descricao'].astype(str).str.lower().str.contains(t_term, na=False) |
                        df_busca_ind['valor'].astype(str).str.contains(t_term, na=False) |
                        df_busca_ind['id'].astype(str).str.contains(t_term, na=False)
                    ]
                    
                if not df_busca_ind.empty:
                    opcoes_map_ind = {}
                    for _, r in df_busca_ind.iterrows():
                        val_fmt = f"R$ {float(r['valor']):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                        dt_ref = r['data_pagamento'] if pd.notna(r.get('data_pagamento')) and r.get('data_pagamento') != '' else r['data_vencimento']
                        label = f"ID #{r['id']} | {r['descricao']} | {val_fmt} | {dt_ref} | {r['banco']} ({r['tipo']})"
                        opcoes_map_ind[label] = int(r['id'])
                        
                    sel_item_label = st.selectbox("Selecione o lançamento correspondente:", list(opcoes_map_ind.keys()), key="sel_item_exc_ind")
                    id_alvo_ind = opcoes_map_ind[sel_item_label]
                    item_alvo_row = df[df['id'] == id_alvo_ind].iloc[0]
                    
                    # Card de Raio-X Detalhado
                    tipo_alvo = str(item_alvo_row['tipo'])
                    id_alvo_str = str(item_alvo_row['id'])
                    st.markdown(f"""
                    <div style="background: rgba(239, 68, 68, 0.08); border: 1px solid rgba(239, 68, 68, 0.35); border-radius: 12px; padding: 16px; margin: 15px 0;">
                        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom: 10px;">
                            <span style="font-weight: 700; color: #F87171; font-size: 0.95rem; text-transform: uppercase; letter-spacing: 0.5px;">
                                🛡️ Raio-X do Lançamento Selecionado (ID #{id_alvo_str})
                            </span>
                            <span style="background: rgba(239, 68, 68, 0.2); color: #FCA5A5; padding: 3px 10px; border-radius: 6px; font-size: 0.75rem; font-weight: 700;">
                                {tipo_alvo}
                            </span>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    rx_col1, rx_col2, rx_col3, rx_col4 = st.columns(4)
                    val_alvo_fmt = f"R$ {float(item_alvo_row['valor']):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                    rx_col1.metric("Valor", val_alvo_fmt)
                    rx_col2.metric("Conta/Banco", str(item_alvo_row['banco']))
                    rx_col3.metric("Data Venc./Compra", str(item_alvo_row['data_vencimento']))
                    rx_col4.metric("Categoria", str(item_alvo_row['categoria_503020']))
                    
                    st.write(f"**Descrição Completa:** `{item_alvo_row['descricao']}`")
                    st.write(f"**Data do Pagamento:** `{item_alvo_row.get('data_pagamento', '-')}` | **Status:** `{item_alvo_row.get('status', '-')}` | **Protocolo:** `{item_alvo_row.get('protocolo', '-')}`")
                    st.markdown("</div>", unsafe_allow_html=True)
                    
                    c_del1, c_del2 = st.columns([1.5, 2.5], vertical_alignment="center")
                    with c_del1:
                        if st.button("🗑️ Confirmar Exclusão Definitiva", type="primary", key="btn_confirma_exc_ind", use_container_width=True):
                            excluir_lancamento(id_alvo_ind)
                            st.success(f"Lançamento ID #{id_alvo_ind} ('{item_alvo_row['descricao']}') excluído com sucesso!")
                            st.rerun()
                    with c_del2:
                        st.caption("⚠️ Esta ação é permanente e atualizará o saldo e extrato instantaneamente.")
                else:
                    st.info("Nenhum lançamento encontrado com os filtros digitados.")
                    
            # --- TAB 2: POR LOTE / IMPORTAÇÃO ---
            with tab_lote:
                st.write("#### 📦 Exclusão por Lote ou Extrato Importado")
                st.caption("Localize uma importação inteira (como uma fatura ou extrato CSV) e visualize todos os itens que a compõem antes de apagar.")
                
                df_com_protocolo = df.dropna(subset=['protocolo']).copy()
                df_com_protocolo = df_com_protocolo[df_com_protocolo['protocolo'] != '']
                
                if not df_com_protocolo.empty:
                    resumo_lotes = df_com_protocolo.groupby('protocolo').agg(
                        banco=('banco', 'first'),
                        qtd=('id', 'count'),
                        total_valor=('valor', 'sum'),
                        dt_min=('data_vencimento', 'min'),
                        dt_max=('data_vencimento', 'max'),
                        exemplo=('descricao', 'first')
                    ).reset_index().sort_values('qtd', ascending=False)
                    
                    opcoes_lote_map = {}
                    for _, row_l in resumo_lotes.iterrows():
                        v_total_fmt = f"R$ {float(row_l['total_valor']):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                        label_lote = f"Lote {row_l['protocolo']} • {row_l['banco']} • {row_l['qtd']} itens (Total {v_total_fmt}) • Período: {row_l['dt_min']} a {row_l['dt_max']} (ex: {row_l['exemplo']})"
                        opcoes_lote_map[label_lote] = row_l['protocolo']
                        
                    sel_lote_label = st.selectbox("Selecione o Lote / Importação:", list(opcoes_lote_map.keys()), key="sel_lote_completo")
                    protocolo_alvo = opcoes_lote_map[sel_lote_label]
                    
                    # Detalhes e Itens do Lote Selecionado
                    itens_do_lote = df_com_protocolo[df_com_protocolo['protocolo'] == protocolo_alvo]
                    
                    st.markdown(f"""
                    <div style="background: rgba(212, 175, 55, 0.08); border: 1px solid rgba(212, 175, 55, 0.3); border-radius: 12px; padding: 14px 18px; margin: 12px 0;">
                        <span style="font-weight: 700; color: #D4AF37; font-size: 0.95rem; text-transform: uppercase;">
                            📋 Itens Contidos no Lote Selecionado ({protocolo_alvo})
                        </span>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    lt1, lt2, lt3 = st.columns(3)
                    lt1.metric("Quantidade de Itens", f"{len(itens_do_lote)} lançamentos")
                    total_lote_calc = f"R$ {itens_do_lote['valor'].sum():,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                    lt2.metric("Valor Total do Lote", total_lote_calc)
                    lt3.metric("Instituição / Origem", str(itens_do_lote['banco'].iloc[0]))
                    
                    st.write("Conferência dos lançamentos que serão apagados juntos:")
                    df_exib_lote = itens_do_lote[['id', 'data_vencimento', 'descricao', 'valor', 'categoria_503020', 'tipo', 'status']].copy()
                    df_exib_lote['valor'] = df_exib_lote['valor'].apply(lambda x: f"R$ {float(x):,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
                    st.dataframe(df_exib_lote, width='stretch', hide_index=True)
                    
                    confirma_lote = st.checkbox(f"Confirmo que revisei a tabela e desejo excluir TODOS os {len(itens_do_lote)} lançamentos do Lote {protocolo_alvo}", key="chk_confirma_lote")
                    
                    if st.button(f"🗑️ Excluir Lote Inteiro ({protocolo_alvo})", type="primary", disabled=not confirma_lote, key="btn_apagar_lote_seguro"):
                        excluir_lancamento_protocolo(protocolo_alvo)
                        st.success(f"Lote {protocolo_alvo} ({len(itens_do_lote)} itens) excluído com sucesso!")
                        st.rerun()
                else:
                    st.info("Nenhum lançamento agrupado por protocolo/lote encontrado.")
                    
            # --- TAB 3: SELEÇÃO MÚLTIPLA POR TABELA ---
            with tab_multi:
                st.write("#### ☑️ Exclusão Rápida por Seleção")
                st.caption("Marque as caixas de seleção dos lançamentos que deseja apagar e confirme a exclusão de todos de uma só vez.")
                
                f_m1, f_m2 = st.columns([2, 1.2])
                with f_m1:
                    filtro_multi_txt = st.text_input("Filtrar itens para seleção:", key="filtro_exc_multi", placeholder="Buscar por nome, valor ou banco...")
                with f_m2:
                    banco_multi = st.selectbox("Banco:", ["Todos"] + sorted(list(df['banco'].dropna().unique())), key="banco_exc_multi")
                    
                df_multi_base = df.copy()
                if banco_multi != "Todos":
                    df_multi_base = df_multi_base[df_multi_base['banco'] == banco_multi]
                if filtro_multi_txt:
                    m_termo = filtro_multi_txt.lower()
                    df_multi_base = df_multi_base[
                        df_multi_base['descricao'].astype(str).str.lower().str.contains(m_termo, na=False) |
                        df_multi_base['valor'].astype(str).str.contains(m_termo, na=False) |
                        df_multi_base['categoria_503020'].astype(str).str.lower().str.contains(m_termo, na=False)
                    ]
                    
                if not df_multi_base.empty:
                    df_para_checar = pd.DataFrame({
                        'Excluir': False,
                        'ID': df_multi_base['id'].values,
                        'Tipo': df_multi_base['tipo'].values,
                        'Descrição': df_multi_base['descricao'].values,
                        'Valor': df_multi_base['valor'].values,
                        'Data': df_multi_base['data_vencimento'].values,
                        'Banco': df_multi_base['banco'].values,
                        'Categoria': df_multi_base['categoria_503020'].values,
                        'Status': df_multi_base['status'].values
                    })
                    
                    config_multi = {
                        "Excluir": st.column_config.CheckboxColumn("Excluir?", help="Marque para excluir este lançamento", default=False),
                        "ID": st.column_config.NumberColumn("ID", disabled=True, width="small"),
                        "Tipo": st.column_config.TextColumn("Tipo", disabled=True, width="small"),
                        "Descrição": st.column_config.TextColumn("Descrição", disabled=True, width="medium"),
                        "Valor": st.column_config.NumberColumn("Valor (R$)", format="R$ %.2f", disabled=True, width="small"),
                        "Data": st.column_config.TextColumn("Data", disabled=True, width="small"),
                        "Banco": st.column_config.TextColumn("Banco", disabled=True, width="small"),
                        "Categoria": st.column_config.TextColumn("Categoria", disabled=True, width="medium"),
                        "Status": st.column_config.TextColumn("Status", disabled=True, width="small"),
                    }
                    
                    df_selecionado = st.data_editor(
                        df_para_checar,
                        column_config=config_multi,
                        disabled=[c for c in df_para_checar.columns if c != "Excluir"],
                        hide_index=True,
                        width='stretch',
                        key="editor_multi_exclusao"
                    )
                    
                    itens_marcados = df_selecionado[df_selecionado['Excluir'] == True]
                    qtd_marcados = len(itens_marcados)
                    
                    if qtd_marcados > 0:
                        total_marcados = itens_marcados['Valor'].sum()
                        val_m_fmt = f"R$ {total_marcados:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                        
                        st.warning(f"⚠️ **{qtd_marcados}** lançamento(s) marcado(s) para exclusão definitiva (Total: **{val_m_fmt}**).")
                        
                        if st.button(f"🗑️ Confirmar Exclusão de {qtd_marcados} Lançamento(s) Marcado(s)", type="primary", key="btn_apaga_marcados", use_container_width=True):
                            ids_a_excluir = itens_marcados['ID'].tolist()
                            excluir_lancamentos_multiplos(ids_a_excluir)
                            st.success(f"🎉 {len(ids_a_excluir)} lançamento(s) excluído(s) com sucesso!")
                            st.rerun()
                    else:
                        st.caption("Marque as caixas de seleção na primeira coluna para ativar o botão de exclusão.")
                else:
                    st.info("Nenhum lançamento disponível para seleção com os filtros atuais.")
                    
        render_footer_economyconty()
    else:
        st.info("Nenhum lançamento encontrado. Cadastre algo na aba ao lado!")
        render_footer_economyconty()

