import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date
import database
from utils import render_footer_economyconty, obter_cor_banco

def render_painel_principal(user_id, nome_usuario="", manu_face_b64=""):
    nome_sessao = nome_usuario
    def listar_lancamentos():
        return database.listar_lancamentos(user_id)
    def obter_saldo_inicial(banco="Itaú", ano=2026):
        return database.obter_saldo_inicial(user_id, banco=banco, ano=ano)
    def salvar_saldo_inicial(banco, ano, valor):
        return database.salvar_saldo_inicial(user_id, banco=banco, ano=ano, valor=valor)

    st.markdown(f"""
    <div style="display: flex; justify-content: space-between; align-items: flex-end; margin-bottom: 1.2rem; padding-bottom: 0.8rem; border-bottom: 1px solid rgba(194, 163, 92, 0.25);">
        <div>
            <h1 style="margin: 0; font-size: 2.1rem; font-weight: 800; background: linear-gradient(90deg, #F9F8F4, #C2A35C); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
                Painel Executivo
            </h1>
            <p style="margin: 4px 0 0 0; color: #9CA3AF; font-size: 0.92rem;"><span class="notranslate" translate="no" style="font-weight: 700; color: #C2A35C;">EconomyContY</span> • Inteligência Financeira e Contábil</p>
        </div>
        <div style="text-align: right;">
            <span class="notranslate" translate="no" style="background: rgba(14, 54, 70, 0.85); border: 1px solid rgba(194, 163, 92, 0.35); border-radius: 8px; padding: 6px 14px; font-size: 0.8rem; color: #F9F8F4; font-weight: 600;">
                🏛️ EconomyContY • Emanuela Freires
            </span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    if manu_face_b64:
        st.html(f"""
        <div class="notranslate" translate="no" style="background: linear-gradient(135deg, rgba(25, 48, 53, 0.9) 0%, rgba(14, 54, 70, 0.95) 100%); border: 1px solid rgba(194, 163, 92, 0.35); border-left: 5px solid #C2A35C; border-radius: 12px; padding: 12px 18px; margin-bottom: 20px; display: flex; align-items: center; gap: 16px; box-shadow: 0 8px 24px rgba(0,0,0,0.3);">
            <img src="data:image/png;base64,{manu_face_b64}" style="width: 56px; height: 56px; border-radius: 50%; border: 2px solid #C2A35C; object-fit: cover; box-shadow: 0 0 10px rgba(194,163,92,0.35);" />
            <div>
                <div style="display: flex; align-items: center; gap: 8px;">
                    <span class="notranslate" translate="no" style="font-family: 'Cinzel', serif; font-size: 1.05rem; font-weight: 700; color: #F9F8F4; letter-spacing: 0.5px;">Manu EconomyContY</span>
                    <span class="notranslate" translate="no" style="background: rgba(194, 163, 92, 0.18); border: 1px solid rgba(194, 163, 92, 0.35); border-radius: 10px; padding: 2px 8px; font-size: 0.70rem; color: #C2A35C; font-weight: 600;">Mentoria & Inteligência</span>
                </div>
                <div style="color: #F9F8F4; font-size: 0.86rem; margin-top: 3px;">
                    Olá, <b>{nome_sessao}</b>! Seu ecossistema financeiro está ativo e consolidado. Todas as contas bancárias, cartões e patrimônio estão conciliados com precisão.
                </div>
            </div>
        </div>
        """)
    
    df = listar_lancamentos()
    if df.empty:
        st.info("Seu banco de dados está vazio. Insira alguns lançamentos para ver o Dashboard!")
    else:
        df['valor'] = pd.to_numeric(df['valor'], errors='coerce').fillna(0.0)
        df['data_vencimento'] = pd.to_datetime(df['data_vencimento'])
        df['data_pagamento'] = pd.to_datetime(df['data_pagamento'])
        
        mes_atual = pd.Timestamp.now().month
        ano_atual = pd.Timestamp.now().year
        
        # Filtros de Mês e Ano
        # Filtros de Mês e Ano + Configuração de Saldo Inicial
        col_m, col_a, col_cfg = st.columns([1, 1, 1.2], vertical_alignment="bottom")
        opcoes_mes = ["Acumulado do Ano"] + list(range(1, 13))
        mes_selecionado = col_m.selectbox("Mês", opcoes_mes, index=mes_atual)
        ano_selecionado = col_a.selectbox("Ano", range(2020, 2030), index=ano_atual-2020)
        
        saldo_inicial_ano = obter_saldo_inicial("Itaú", ano_selecionado)
        
        with col_cfg:
            with st.popover(f"🏦 Saldo Inicial ({ano_selecionado})", use_container_width=True):
                st.write(f"**Saldo Inicial da Conta em 01/01/{ano_selecionado}**")
                st.caption("Informe quanto havia na conta corrente no início do ano. O sistema calcula e transporta a disponibilidade mês a mês automaticamente.")
                novo_saldo_ini = st.number_input("Saldo em 01/01 (R$):", value=float(saldo_inicial_ano), format="%.2f", step=100.0, key=f"saldo_ini_input_{ano_selecionado}")
                if st.button("Salvar Saldo Inicial", type="primary", key=f"btn_salvar_ini_{ano_selecionado}"):
                    salvar_saldo_inicial("Itaú", ano_selecionado, novo_saldo_ini)
                    st.success("Saldo inicial salvo com sucesso!")
                    st.rerun()
        
        if mes_selecionado == "Acumulado do Ano":
            df_mes = df[df['data_pagamento'].dt.year == ano_selecionado]
            titulo_resumo = f"### 💰 Resumo Financeiro Acumulado de {ano_selecionado}"
            saldo_inicial_periodo = saldo_inicial_ano
            rotulo_resultado = "Resultado do Ano"
        else:
            df_mes = df[(df['data_pagamento'].dt.month == mes_selecionado) & (df['data_pagamento'].dt.year == ano_selecionado)]
            titulo_resumo = f"### 💰 Resumo Financeiro do Mês {mes_selecionado}/{ano_selecionado}"
            rotulo_resultado = "Resultado do Mês"
            
            # Transporta o resultado dos meses anteriores do ano
            df_anteriores = df[(df['data_pagamento'].dt.year == ano_selecionado) & (df['data_pagamento'].dt.month < mes_selecionado)]
            rec_ant = df_anteriores[df_anteriores['tipo'].isin(['Receita', 'Outras Receitas', 'Resgate de Investimento'])]['valor'].sum()
            desp_ant = df_anteriores[df_anteriores['tipo'] == 'Despesa']['valor'].sum()
            saldo_acum_anterior = rec_ant - desp_ant
            saldo_inicial_periodo = saldo_inicial_ano + saldo_acum_anterior
        
        # --- MÉTRICAS ---
        receitas = df_mes[df_mes['tipo'] == 'Receita']['valor'].sum()
        outras_receitas = df_mes[df_mes['tipo'] == 'Outras Receitas']['valor'].sum()
        resgates = df_mes[df_mes['tipo'] == 'Resgate de Investimento']['valor'].sum()
        total_entradas = receitas + outras_receitas + resgates
        
        despesas = df_mes[df_mes['tipo'] == 'Despesa']['valor'].sum()
        saldo = total_entradas - despesas
        disponibilidade_final = saldo_inicial_periodo + saldo
        
        st.write(titulo_resumo)
        
        # Linha 1: Entradas (Receitas Fixas, Outras Receitas, Resgates)
        st.markdown("<p style='font-size:0.78rem; font-weight:700; color:#34D399; text-transform:uppercase; letter-spacing:1px; margin-bottom:4px;'>📥 Entradas de Recursos</p>", unsafe_allow_html=True)
        col_r1, col_r2, col_r3 = st.columns(3)
        with col_r1:
            st.metric("Salário / Receita Fixa", f"R$ {receitas:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
            with st.expander("🔍 Detalhes (Fixas)"):
                st.dataframe(df_mes[df_mes['tipo'] == 'Receita'][['data_vencimento', 'descricao', 'valor', 'banco']], hide_index=True, use_container_width=True)
        with col_r2:
            st.metric("Outras Receitas", f"R$ {outras_receitas:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
            with st.expander("🔍 Detalhes (Outras)"):
                st.dataframe(df_mes[df_mes['tipo'] == 'Outras Receitas'][['data_vencimento', 'descricao', 'valor', 'banco']], hide_index=True, use_container_width=True)
        with col_r3:
            st.metric("Resgates de Investimentos", f"R$ {resgates:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
            with st.expander("🔍 Detalhes (Resgates)"):
                st.dataframe(df_mes[df_mes['tipo'] == 'Resgate de Investimento'][['data_vencimento', 'descricao', 'valor', 'banco']], hide_index=True, use_container_width=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # Linha 2: Saídas e Disponibilidades
        st.markdown("<p style='font-size:0.78rem; font-weight:700; color:#F87171; text-transform:uppercase; letter-spacing:1px; margin-bottom:4px;'>📤 Saídas & Posição de Caixa</p>", unsafe_allow_html=True)
        col_s1, col_s2, col_s3 = st.columns(3)
        with col_s1:
            st.metric("Despesas Totais", f"R$ {despesas:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
            with st.expander("🔍 Detalhes (Despesas)"):
                st.dataframe(df_mes[df_mes['tipo'] == 'Despesa'][['data_vencimento', 'descricao', 'valor', 'banco', 'categoria_503020']], hide_index=True, use_container_width=True)
        with col_s2:
            st.metric(rotulo_resultado, f"R$ {saldo:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."), delta=f"R$ {saldo:,.2f}", delta_color="normal" if saldo >= 0 else "inverse")
            with st.expander("🔍 Balanço"):
                st.write(f"**Receita Fixa:** +R$ {receitas:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
                st.write(f"**Outras Receitas:** +R$ {outras_receitas:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
                if resgates > 0:
                    st.write(f"**Resgates:** +R$ {resgates:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
                st.write(f"**Total Entradas:** +R$ {total_entradas:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
                st.write(f"**Saídas:** -R$ {despesas:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
                st.write(f"**Resultado:** R$ {saldo:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        with col_s3:
            saldo_ini_fmt = f"R$ {saldo_inicial_periodo:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            st.metric("Disponibilidade em Conta", f"R$ {disponibilidade_final:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."), delta=f"Saldo Inicial: {saldo_ini_fmt}", delta_color="off")
            with st.expander("🔍 Composição da Conta"):
                st.write(f"**Saldo Inicial:** {saldo_ini_fmt}")
                st.write(f"**Total Entradas:** +R$ {total_entradas:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
                st.write(f"**Saídas:** -R$ {despesas:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
                st.write(f"**Resultado:** R$ {saldo:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
                st.write(f"**Disponibilidade:** R$ {disponibilidade_final:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        
        st.markdown("---")
        # --- REGRA 50/30/20 ---
        st.write("### 🎯 Termômetro da Regra 50/30/20")
        st.write("A regra sugere que você destine no máximo **50%** para Necessidades, **30%** para Desejos, e invista ou construa patrimônio com no mínimo **20%**.")
        
        if despesas > 0:
            df_despesas = df_mes[df_mes['tipo'] == 'Despesa']
            
            nec = df_despesas[df_despesas['categoria_503020'] == 'Necessidade (50%)']['valor'].sum()
            desejo = df_despesas[df_despesas['categoria_503020'] == 'Desejo (30%)']['valor'].sum()
            poup = df_despesas[df_despesas['categoria_503020'] == 'Investimento (20%)']['valor'].sum()
            
            pct_nec = (nec / despesas) * 100
            pct_desejo = (desejo / despesas) * 100
            pct_poup = (poup / despesas) * 100
            
            val_nec_fmt = f"R$ {nec:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            val_des_fmt = f"R$ {desejo:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            val_poup_fmt = f"R$ {poup:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            
            c1, c2, c3 = st.columns(3)
            
            # Necessidades
            with c1:
                st.markdown(f"""
                <div class="thermo-card">
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
                        <span style="font-weight:700; color:#F3E5AB; font-size:0.95rem;">Necessidades</span>
                        <span style="background:rgba(212,175,55,0.15); color:#D4AF37; padding:2px 8px; border-radius:6px; font-size:0.75rem; font-weight:600;">Meta: máx 50%</span>
                    </div>
                    <div style="font-size:1.8rem; font-weight:800; color:{'#EF4444' if pct_nec > 50 else '#10B981'}; margin-bottom:4px;">
                        {pct_nec:.1f}%
                    </div>
                    <div style="color:#9CA3AF; font-size:0.85rem; margin-bottom:10px;">{val_nec_fmt}</div>
                </div>
                """, unsafe_allow_html=True)
                st.progress(min(max(pct_nec / 100.0, 0.0), 1.0))
            
            # Desejos
            with c2:
                st.markdown(f"""
                <div class="thermo-card">
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
                        <span style="font-weight:700; color:#F3E5AB; font-size:0.95rem;">Desejos & Estilo</span>
                        <span style="background:rgba(212,175,55,0.15); color:#D4AF37; padding:2px 8px; border-radius:6px; font-size:0.75rem; font-weight:600;">Meta: máx 30%</span>
                    </div>
                    <div style="font-size:1.8rem; font-weight:800; color:{'#EF4444' if pct_desejo > 30 else '#10B981'}; margin-bottom:4px;">
                        {pct_desejo:.1f}%
                    </div>
                    <div style="color:#9CA3AF; font-size:0.85rem; margin-bottom:10px;">{val_des_fmt}</div>
                </div>
                """, unsafe_allow_html=True)
                st.progress(min(max(pct_desejo / 100.0, 0.0), 1.0))
            
            # Investimento (Despesas classificadas como investimento, ex: lote/casa)
            with c3:
                st.markdown(f"""
                <div class="thermo-card">
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
                        <span style="font-weight:700; color:#F3E5AB; font-size:0.95rem;">Construção de Patrimônio</span>
                        <span style="background:rgba(16,185,129,0.15); color:#34D399; padding:2px 8px; border-radius:6px; font-size:0.75rem; font-weight:600;">Meta: mín 20%</span>
                    </div>
                    <div style="font-size:1.8rem; font-weight:800; color:{'#EF4444' if pct_poup < 20 else '#10B981'}; margin-bottom:4px;">
                        {pct_poup:.1f}%
                    </div>
                    <div style="color:#9CA3AF; font-size:0.85rem; margin-bottom:10px;">{val_poup_fmt}</div>
                </div>
                """, unsafe_allow_html=True)
                st.progress(min(max(pct_poup / 100.0, 0.0), 1.0))
            
        else:
            st.info("Cadastre alguma Despesa no período selecionado para ver o termômetro do 50/30/20!")
            
        st.markdown("---")
        # --- GRÁFICOS ---
        
        c_graf1, c_graf2 = st.columns(2)
        
        with c_graf1:
            st.write("#### 💸 Despesas por Categoria")
            if despesas > 0:
                cores_cat_pizza = {
                    'Necessidade (50%)': '#4E89AE',   # Azul Ardósia Suave
                    'Desejo (30%)': '#D97736',        # Âmbar / Terracota Suave
                    'Investimento (20%)': '#42986E',   # Verde Sálvia / Esmeralda Suave
                    'Renda (Não se aplica)': '#8E9AA8' # Cinza Neutro Suave
                }
                fig_cat = px.pie(
                    df_mes[df_mes['tipo'] == 'Despesa'], 
                    values='valor', 
                    names='categoria_503020', 
                    hole=0.45, 
                    color='categoria_503020',
                    color_discrete_map=cores_cat_pizza
                )
                fig_cat.update_traces(
                    opacity=0.90,
                    marker=dict(line=dict(color='#080E18', width=2))
                )
                fig_cat.update_layout(
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    font=dict(family="Plus Jakarta Sans", color="#F9FAFB"),
                    legend=dict(orientation="h", yanchor="bottom", y=-0.25, xanchor="center", x=0.5)
                )
                st.plotly_chart(fig_cat, use_container_width=True)
            else:
                st.write("Sem despesas para exibir.")
                
        with c_graf2:
            st.write("#### 🏛️ Gastos por Banco/Cartão")
            if despesas > 0:
                # Calcula despesas por banco
                desp_banco = df_mes[df_mes['tipo'] == 'Despesa'].groupby('banco')['valor'].sum().reset_index()
                
                # Verifica estornos (Receitas atreladas a faturas de cartão)
                estornos = df_mes[(df_mes['tipo'] == 'Receita') & (df_mes['banco'].str.contains('Cartão', case=False, na=False))].groupby('banco')['valor'].sum().reset_index()
                
                if not estornos.empty:
                    bancos = pd.merge(desp_banco, estornos, on='banco', how='left', suffixes=('', '_estorno'))
                    bancos['valor_estorno'] = bancos['valor_estorno'].fillna(0)
                    bancos['valor'] = bancos['valor'] - bancos['valor_estorno']
                else:
                    bancos = desp_banco
                    
                mapa_cores_banco = {b: obter_cor_banco(b) for b in bancos['banco'].unique()}
                fig_banco = px.bar(
                    bancos, 
                    x='banco', 
                    y='valor', 
                    text_auto='.2s', 
                    color='banco', 
                    color_discrete_map=mapa_cores_banco
                )
                fig_banco.update_traces(
                    opacity=0.88,
                    marker=dict(line=dict(width=1, color='rgba(255,255,255,0.08)'))
                )
                fig_banco.update_layout(
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    font=dict(family="Plus Jakarta Sans", color="#F9FAFB"),
                    xaxis=dict(showgrid=False),
                    yaxis=dict(gridcolor="rgba(212, 175, 55, 0.1)")
                )
                st.plotly_chart(fig_banco, use_container_width=True)
            else:
                st.write("Sem despesas para exibir.")
                
        st.markdown("---")
        # --- VALIDAÇÃO DE IRPF ---
        st.write("### 🦁 Extrato Anual de IRPF")
        st.write("Visualize os totais retidos (IRRF) e os rendimentos (INSS) recebidos durante o ano para facilitar a sua declaração.")
        
        df_ano = df[(df['data_vencimento'].dt.year == ano_selecionado)]
        irrf_linhas = df_ano[df_ano['descricao'].str.contains("IRRF", case=False, na=False) | df_ano['descricao'].str.contains("Imposto de Renda", case=False, na=False)]
        
        # Rendimentos Tributáveis: Banco INSS ou marcado manualmente no checkbox
        if 'tributavel' in df_ano.columns:
            inss_linhas = df_ano[(df_ano['banco'] == "INSS") | (df_ano['tributavel'] == 1)]
        else:
            inss_linhas = df_ano[df_ano['banco'] == "INSS"]
        
        c_irpf1, c_irpf2 = st.columns(2)
        
        with c_irpf1:
            st.write("#### 💸 IRRF Retido")
            if irrf_linhas.empty:
                st.info(f"Nenhum lançamento de IRRF encontrado em {ano_selecionado}.")
            else:
                total_irrf = irrf_linhas['valor'].sum()
                st.metric(f"Total Retido ({ano_selecionado})", f"R$ {total_irrf:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
                st.dataframe(irrf_linhas[['data_vencimento', 'descricao', 'valor']], hide_index=True)
                
        with c_irpf2:
            st.write("#### 🏢 Rendimentos Tributáveis")
            total_inss = 0
            if inss_linhas.empty:
                st.info(f"Nenhum rendimento tributável encontrado em {ano_selecionado}.")
            else:
                total_inss = inss_linhas['valor'].sum()
                st.metric(f"Rendimentos Tributáveis ({ano_selecionado})", f"R$ {total_inss:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
                st.dataframe(inss_linhas[['data_vencimento', 'descricao', 'valor']], hide_index=True)
                
        # --- CÁLCULO DE IRPF ---
        st.write("#### 🧮 Simulação de Declaração (Tabela Anual Vigente)")
        
        if 'dedutivel' in df_ano.columns:
            despesas_dedutiveis = df_ano[(df_ano['tipo'] == 'Despesa') & (df_ano['dedutivel'] == 1)]
            total_deducoes = despesas_dedutiveis['valor'].sum()
        else:
            total_deducoes = 0.0
            
        desconto_simplificado = min(total_inss * 0.20, 16754.34)
        
        # O melhor desconto para o usuário
        melhor_deducao = max(total_deducoes, desconto_simplificado)
        base_calculo = total_inss - melhor_deducao
        if base_calculo < 0: base_calculo = 0
        
        # Tabela Progressiva Anual
        if base_calculo <= 28559.70:
            imposto_devido = 0.0
        elif base_calculo <= 33919.80:
            imposto_devido = (base_calculo * 0.075) - 2141.98
        elif base_calculo <= 45012.60:
            imposto_devido = (base_calculo * 0.15) - 4685.96
        elif base_calculo <= 55976.16:
            imposto_devido = (base_calculo * 0.225) - 8061.91
        else:
            imposto_devido = (base_calculo * 0.275) - 10860.71
            
        if imposto_devido < 0: imposto_devido = 0.0
        
        total_irrf = irrf_linhas['valor'].sum() if not irrf_linhas.empty else 0.0
        saldo_imposto = imposto_devido - total_irrf
        
        c_sim1, c_sim2, c_sim3 = st.columns(3)
        with c_sim1:
            st.metric("Deduções Legais (Saúde/Educação)", f"R$ {total_deducoes:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
            if total_deducoes > desconto_simplificado:
                st.caption("✅ Modelo Completo é mais vantajoso.")
            else:
                st.caption("❌ Modelo Simplificado (R$ 16.754) é melhor.")
        
        with c_sim2:
            st.metric("Imposto Devido (Antes das retenções)", f"R$ {imposto_devido:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
            
        with c_sim3:
            if saldo_imposto > 0:
                st.error(f"🔴 IMPOSTO A PAGAR: R$ {saldo_imposto:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
            elif saldo_imposto < 0:
                st.success(f"🟢 RESTITUIÇÃO A RECEBER: R$ {abs(saldo_imposto):,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
            else:
                st.info("⚪ NADA A PAGAR OU RECEBER")
        
        st.markdown("""
        <div class="notranslate" translate="no" style="text-align: center; margin-top: 50px; padding: 24px 0 10px 0; border-top: 1px solid rgba(212, 175, 55, 0.15); font-size: 0.8rem; color: #9CA3AF;">
            <div style="font-weight: 700; color: #D4AF37; letter-spacing: 1px; font-size: 0.95rem;">EconomyContY</div>
            <div style="margin: 4px 0;">Plataforma Integrada de Inteligência Contábil & Gestão Financeira</div>
            <div style="margin-top: 6px;">
                <span style="background: rgba(212, 175, 55, 0.1); border: 1px solid rgba(212, 175, 55, 0.25); border-radius: 6px; padding: 3px 10px; color: #F3E5AB; font-weight: 600;">
                    © Todos os direitos reservados • Emanuela Freires
                </span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
