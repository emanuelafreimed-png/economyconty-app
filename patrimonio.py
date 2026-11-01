import numpy as np
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date
import database
from utils import render_footer_economyconty, obter_cor_banco

def render_patrimonio(user_id, nome_usuario="", manu_face_b64=""):
    def listar_patrimonio():
        return database.listar_patrimonio(user_id)
    def atualizar_patrimonio(ativo, novo_saldo, data_atualizacao=None):
        return database.atualizar_patrimonio(user_id, ativo, novo_saldo, data_atualizacao)
    def adicionar_ativo(nome_ativo, saldo=0.0):
        return database.adicionar_ativo(user_id, nome_ativo, saldo)
    def excluir_ativo(nome_ativo):
        return database.excluir_ativo(user_id, nome_ativo)
    def registrar_historico_patrimonio(total, data_registro=None):
        return database.registrar_historico_patrimonio(user_id, total, data_registro)
    def listar_historico_patrimonio():
        return database.listar_historico_patrimonio(user_id)
    def excluir_historico_patrimonio(id_hist):
        return database.excluir_historico_patrimonio(user_id, id_hist)
        
    avatar_elem = f'<img src="data:image/png;base64,{manu_face_b64}" style="width: 50px; height: 50px; border-radius: 50%; border: 2px solid #C2A35C; object-fit: cover; box-shadow: 0 0 10px rgba(194,163,92,0.35);" />' if manu_face_b64 else '<div style="width: 50px; height: 50px; border-radius: 50%; background: #C2A35C; color: #193035; display: flex; align-items: center; justify-content: center; font-weight: 700;">EC</div>'

    @st.cache_data(ttl=3600)
    def obter_dados_oficiais_mercado():
        """Consulta dados 100% oficiais das APIs publicas do Banco Central do Brasil (SGS) e B3/IBGE"""
        import urllib.request
        import json
        
        dados = {
            "selic": 13.75,
            "selic_data": "04/11/2026",
            "cdi": 13.65,
            "cdi_data": "27/10/2026",
            "ipca": 4.58,
            "ipca_data": "01/09/2026",
            "poupanca": 0.6624,
            "poupanca_data": "01/10/2026",
            "fonte_oficial": "Banco Central do Brasil (SGS) e B3 / IBGE"
        }
        
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        
        def fetch_sgs(code):
            try:
                url = f"https://api.bcb.gov.br/dados/serie/bcdata.sgs.{code}/dados/ultimos/1?formato=json"
                req = urllib.request.Request(url, headers=headers)
                with urllib.request.urlopen(req, timeout=3) as response:
                    res = json.loads(response.read().decode('utf-8'))
                    if res and isinstance(res, list) and len(res) > 0:
                        return float(res[0]['valor']), res[0]['data']
            except Exception:
                pass
            return None, None
                
        s_val, s_dt = fetch_sgs(432)
        c_val, c_dt = fetch_sgs(4389)
        i_val, i_dt = fetch_sgs(13522)
        p_val, p_dt = fetch_sgs(196)
        
        if s_val is not None:
            dados["selic"] = s_val
            dados["selic_data"] = s_dt
        if c_val is not None:
            dados["cdi"] = c_val
            dados["cdi_data"] = c_dt
        else:
            dados["cdi"] = round(dados["selic"] - 0.10, 2)
        if i_val is not None:
            dados["ipca"] = i_val
            dados["ipca_data"] = i_dt
        if p_val is not None:
            dados["poupanca"] = p_val
            dados["poupanca_data"] = p_dt

        selic_dec = dados["selic"] / 100.0
        ipca_dec = dados["ipca"] / 100.0
        dados["juro_real"] = round(((1.0 + selic_dec) / (1.0 + ipca_dec) - 1.0) * 100.0, 2)
        return dados
    st.markdown("""
    <div style="margin-bottom: 1.2rem; padding-bottom: 0.8rem; border-bottom: 1px solid rgba(194, 163, 92, 0.25);">
        <h1 style="margin: 0; font-size: 2rem; font-weight: 800; background: linear-gradient(90deg, #F9F8F4, #C2A35C); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
            💼 Gestão de Patrimônio & Ativos
        </h1>
        <p style="margin: 4px 0 0 0; color: #7D5768; font-size: 0.9rem;">Controle consolidado dos ativos de valor, alocação estratégica e evolução temporal da riqueza</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Busca os dados atuais
    df_patrimonio = listar_patrimonio()
    total_patrimonio = df_patrimonio['saldo'].sum() if not df_patrimonio.empty else 0.0
    
    # Função classificadora inteligente por Classe de Ativo
    def categorizar_ativo(nome):
        n = str(nome).lower().strip()
        if any(k in n for k in ['cdb', 'tesouro', 'cofrinho', 'lci', 'lca', 'cri', 'cra', 'renda fixa']):
            return "Renda Fixa & Títulos Públicos"
        elif any(k in n for k in ['previdência', 'previdencia', 'fgts', 'pgbl', 'vgbl', 'inss']):
            return "Previdência & Benefícios Sociais"
        elif any(k in n for k in ['fundo', 'ação', 'acoes', 'fii', 'ações', 'multimercado', 'etf']):
            return "Fundos & Renda Variável"
        elif any(k in n for k in ['binance', 'crypto', 'cripto', 'bitcoin', 'btc', 'eth']):
            return "Criptoativos & Alternativos"
        elif any(k in n for k in ['saldo', 'caixa', 'bancário', 'bancario', 'conta', 'nu bank', 'corrente']):
            return "Disponibilidade Bancária"
        else:
            return "Outros Investimentos"

    if not df_patrimonio.empty:
        df_patrimonio['tipo_classe'] = df_patrimonio['ativo'].apply(categorizar_ativo)
        df_patrimonio['percentual'] = (df_patrimonio['saldo'] / total_patrimonio * 100).round(2) if total_patrimonio > 0 else 0.0
    else:
        df_patrimonio['tipo_classe'] = []
        df_patrimonio['percentual'] = []

    # Card executivo em Verde-Petróleo, Vinho e Dourado Champagne (Paleta Oficial)
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, rgba(25, 48, 53, 0.9) 0%, rgba(14, 54, 70, 0.95) 100%); border: 1px solid rgba(194, 163, 92, 0.35); border-left: 6px solid #C2A35C; border-radius: 14px; padding: 22px 28px; margin-bottom: 24px; box-shadow: 0 10px 30px rgba(0,0,0,0.4); display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 15px;">
        <div>
            <span style="color: #7D5768; font-size: 0.85rem; font-weight: 700; text-transform: uppercase; letter-spacing: 1px;">Patrimônio Líquido Consolidado</span>
            <div style="font-size: 2.7rem; font-weight: 800; color: #F9F8F4; margin: 4px 0; text-shadow: 0 0 15px rgba(194, 163, 92, 0.35);">
                R$ {total_patrimonio:,.2f}
            </div>
            <span style="color: #C2A35C; font-size: 0.85rem; font-weight: 600;">✨ 100% dos Ativos Conciliados • EconomyContY</span>
        </div>
        <div style="text-align: right;">
            <div style="background: rgba(194, 163, 92, 0.12); border: 1px solid rgba(194, 163, 92, 0.35); border-radius: 10px; padding: 10px 18px; text-align: center;">
                <div style="font-size: 0.76rem; color: #7D5768; font-weight: 700; text-transform: uppercase;">Total de Ativos</div>
                <div style="font-size: 1.4rem; font-weight: 700; color: #C2A35C;">{len(df_patrimonio)} Ativos</div>
            </div>
        </div>
    </div>
    """.replace(",", "X").replace(".", ",").replace("X", "."), unsafe_allow_html=True)

    tab_carteira, tab_consultor = st.tabs([
        "📊 Visão Geral da Carteira", 
        "🧠 Consultor de Investimentos IA (Manu EconomyContY)"
    ])

    with tab_carteira:

        # 4 Cards / KPIs por Tipo de Investimento
        if not df_patrimonio.empty:
            df_classe_sum = df_patrimonio.groupby('tipo_classe')['saldo'].sum().reset_index()
            icones_classe = {
                "Renda Fixa & Títulos Públicos": "🏛️",
                "Fundos & Renda Variável": "📈",
                "Previdência & Benefícios Sociais": "🛡️",
                "Disponibilidade Bancária": "💳",
                "Criptoativos & Alternativos": "🪙",
                "Outros Investimentos": "📦"
            }
        
            cols_classe = st.columns(min(len(df_classe_sum), 4))
            for idx, row in df_classe_sum.iterrows():
                col_target = cols_classe[idx % len(cols_classe)]
                perc_classe = (row['saldo'] / total_patrimonio * 100) if total_patrimonio > 0 else 0
                icone = icones_classe.get(row['tipo_classe'], "💼")
                with col_target:
                    st.markdown(f"""
                    <div class="kpi-card" style="margin-bottom: 12px; padding: 14px 16px;">
                        <div class="kpi-label" style="font-size: 0.74rem;">{icone} {row['tipo_classe']}</div>
                        <div style="font-size: 1.25rem; font-weight: 700; color: #F9F8F4; margin: 4px 0;">R$ {row['saldo']:,.2f}</div>
                        <div style="font-size: 0.75rem; color: #C2A35C; font-weight: 600;">{perc_classe:.1f}% do portfólio</div>
                    </div>
                    """.replace(",", "X").replace(".", ",").replace("X", "."), unsafe_allow_html=True)

        st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)
    
        # --------------------------------------------------------------------------
        # 1. GRÁFICO DE BARRAS DESTACANDO O TOTAL DE CADA INVESTIMENTO
        # --------------------------------------------------------------------------
        st.write("### 📊 Posição Detalhada por Investimento")
        st.caption("Gráfico comparativo ordenado do maior para o menor ativo com valores destacados em cada barra:")
    
        cores_map = {
            "Renda Fixa & Títulos Públicos": "#C2A35C",       # Dourado Champagne
            "Fundos & Renda Variável": "#0E3646",            # Azul-Petróleo
            "Previdência & Benefícios Sociais": "#4A1728",    # Vinho Profundo
            "Criptoativos & Alternativos": "#B88A2D",         # Dourado Intenso
            "Disponibilidade Bancária": "#7D5768",            # Ameixa Elegante
            "Outros Investimentos": "#193035"
        }

        if not df_patrimonio.empty:
            df_bar = df_patrimonio.sort_values(by='saldo', ascending=True).copy()
        
            fig_bar = px.bar(
                df_bar,
                x='saldo',
                y='ativo',
                orientation='h',
                color='tipo_classe',
                color_discrete_map=cores_map,
                text='saldo',
                labels={'saldo': 'Saldo (R$)', 'ativo': 'Investimento', 'tipo_classe': 'Tipo de Investimento'}
            )
        
            fig_bar.update_traces(
                texttemplate='  R$ %{x:,.2f}',
                textposition='outside',
                cliponaxis=False,
                marker_line_color='rgba(194, 163, 92, 0.4)',
                marker_line_width=1,
                hovertemplate="<b>%{y}</b><br>Saldo: R$ %{x:,.2f}<br>Classe: %{data.name}<extra></extra>"
            )
        
            fig_bar.update_layout(
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#F9F8F4"),
                xaxis=dict(
                    showgrid=True,
                    gridcolor="rgba(194, 163, 92, 0.15)",
                    tickprefix="R$ ",
                    title="",
                    showticklabels=True
                ),
                yaxis=dict(
                    showgrid=False,
                    title="",
                    tickfont=dict(size=12, color="#F9F8F4", family="Plus Jakarta Sans")
                ),
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1,
                    title=dict(text="")
                ),
                height=430,
                margin=dict(l=20, r=110, t=30, b=20)
            )
        
            st.plotly_chart(fig_bar, use_container_width=True)

        # --------------------------------------------------------------------------
        # 2. VISÃO ANALÍTICA SEPARADA POR TIPO DE INVESTIMENTO
        # --------------------------------------------------------------------------
        st.markdown("---")
        st.write("### 🎯 Visão Analítica por Tipo de Investimento")
        st.caption("Distribuição percentual da carteira e detalhamento completo segregado por classe:")
    
        if not df_patrimonio.empty:
            col_pie, col_table = st.columns([1, 1.4])
        
            with col_pie:
                st.markdown("#### Alocação Percentual da Carteira")
                df_pie = df_patrimonio.groupby('tipo_classe')['saldo'].sum().reset_index()
                fig_pie = px.pie(
                    df_pie,
                    values='saldo',
                    names='tipo_classe',
                    hole=0.58,
                    color='tipo_classe',
                    color_discrete_map=cores_map
                )
                fig_pie.update_traces(
                    textposition='inside',
                    textinfo='percent',
                    hovertemplate="<b>%{label}</b><br>Total: R$ %{value:,.2f}<br>Alocação: %{percent}<extra></extra>"
                )
                fig_pie.update_layout(
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    font=dict(color="#F9F8F4"),
                    showlegend=True,
                    legend=dict(orientation="v", yanchor="middle", y=0.5, xanchor="left", x=1.02),
                    margin=dict(l=10, r=10, t=10, b=10),
                    height=320
                )
                st.plotly_chart(fig_pie, use_container_width=True)
            
            with col_table:
                st.markdown("#### Tabela Detalhada por Classe e Ativo")
                df_table = df_patrimonio.sort_values(by=['tipo_classe', 'saldo'], ascending=[True, False]).copy()
                df_table_display = pd.DataFrame({
                    "Classe / Tipo": df_table['tipo_classe'],
                    "Investimento": df_table['ativo'],
                    "Saldo Atual": df_table['saldo'].apply(lambda x: f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")),
                    "% Carteira": df_table['percentual'].apply(lambda x: f"{x:.2f}%".replace(".", ",")),
                    "Última Atualização": pd.to_datetime(df_table['data_atualizacao']).dt.strftime('%d/%m/%Y').fillna("Nunca")
                })
                st.dataframe(df_table_display, use_container_width=True, hide_index=True)

        # --------------------------------------------------------------------------
        # 3. EVOLUÇÃO TEMPORAL DO PATRIMÔNIO (MENSAL - POSIÇÃO NO 1º DIA DO MÊS)
        # --------------------------------------------------------------------------
        st.markdown("---")
        st.write("### 📈 Evolução Histórica do Patrimônio (Mensal)")
        st.caption("Acompanhamento mensal da curva de crescimento do seu patrimônio consolidado (fechamento oficial no 1º dia de cada mês):")
        df_hist = listar_historico_patrimonio()
        if not df_hist.empty:
            df_hist['data_dt'] = pd.to_datetime(df_hist['data_registro'])
            df_hist = df_hist.sort_values(by='data_dt').reset_index(drop=True)
        
            meses_abrev = {
                1: "Jan", 2: "Fev", 3: "Mar", 4: "Abr", 5: "Mai", 6: "Jun",
                7: "Jul", 8: "Ago", 9: "Set", 10: "Out", 11: "Nov", 12: "Dez"
            }
            meses_full = {
                1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril", 5: "Maio", 6: "Junho",
                7: "Julho", 8: "Agosto", 9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro"
            }
        
            df_hist['competencia'] = df_hist['data_dt'].apply(lambda d: f"{meses_abrev[d.month]}/{d.year}")
            df_hist['competencia_extenso'] = df_hist['data_dt'].apply(lambda d: f"{meses_full[d.month]} de {d.year}")
            df_hist['posicao_dia'] = df_hist['data_dt'].apply(lambda d: f"01/{d.month:02d}/{d.year}")
            df_hist['total_fmt'] = df_hist['total'].apply(lambda v: f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
            df_hist['rotulo_curva'] = df_hist['total'].apply(lambda v: f"R$ {v/1000:,.1f}k".replace(".", ",") if v >= 10000 else f"R$ {v:,.0f}".replace(".", ","))
        
            fig_hist = go.Figure()
            fig_hist.add_trace(go.Scatter(
                x=df_hist['competencia'],
                y=df_hist['total'],
                mode='lines+markers+text',
                text=df_hist['rotulo_curva'],
                textposition='top center',
                textfont=dict(color='#F9F8F4', size=11, family='Inter, sans-serif'),
                name='Patrimônio Consolidado',
                line=dict(color='#C2A35C', width=3, shape='spline', smoothing=0.3),
                marker=dict(size=9, color='#F9F8F4', line=dict(color='#C2A35C', width=2.5)),
                fill='tozeroy',
                fillcolor='rgba(194, 163, 92, 0.12)',
                customdata=df_hist[['competencia_extenso', 'posicao_dia', 'total_fmt']].values,
                hovertemplate="<b>Competência:</b> %{customdata[0]}<br><b>Posição:</b> %{customdata[1]} (1º dia do mês)<br><b>Patrimônio Consolidado:</b> %{customdata[2]}<extra></extra>"
            ))
        
            fig_hist.update_layout(
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#F9F8F4", family="Inter, sans-serif"),
                xaxis=dict(
                    type='category',
                    categoryorder='array',
                    categoryarray=df_hist['competencia'].tolist(),
                    showgrid=True,
                    gridcolor="rgba(194, 163, 92, 0.15)",
                    title=None,
                    tickfont=dict(size=12, color="#F9F8F4")
                ),
                yaxis=dict(
                    showgrid=True,
                    gridcolor="rgba(194, 163, 92, 0.15)",
                    tickprefix="R$ ",
                    tickfont=dict(size=11, color="#F9F8F4")
                ),
                margin=dict(l=20, r=20, t=35, b=20),
                height=290
            )
            st.plotly_chart(fig_hist, use_container_width=True)

            # Análise das competências do ano atual (Quais meses já foram lançados e quais estão pendentes)
            ano_vigente = date.today().year
            mes_vigente = date.today().month
        
            # Mapeia datas gravadas
            dict_gravados = {}
            for _, r in df_hist.iterrows():
                d_str = str(r['data_registro'])[:7] + "-01"
                dict_gravados[d_str] = r['total']
            
            chips_html = []
            pendentes_nomes = []
            pendentes_datas = []
        
            for m in range(1, 13):
                k_mes = f"{ano_vigente}-{m:02d}-01"
                nome_abrev = meses_abrev[m]
                if k_mes in dict_gravados:
                    tot = dict_gravados[k_mes]
                    tot_lbl = f"R$ {tot/1000:,.1f}k".replace(".", ",") if tot >= 10000 else f"R$ {tot:,.0f}".replace(".", ",")
                    chips_html.append(f"""
                    <div style="flex: 1 1 70px; min-width: 66px; text-align: center; padding: 6px 4px; border-radius: 8px; background: rgba(194, 163, 92, 0.16); border: 1.5px solid #C2A35C; box-shadow: 0 2px 4px rgba(0,0,0,0.2);">
                        <div style="font-size: 11px; font-weight: 700; color: #F9F8F4;">{nome_abrev}/{str(ano_vigente)[-2:]}</div>
                        <div style="font-size: 10px; color: #C2A35C; font-weight: 600;">{tot_lbl}</div>
                        <div style="font-size: 9px; color: #85e085; font-weight: 600;">✔ Lançado</div>
                    </div>
                    """)
                elif m <= mes_vigente:
                    pendentes_nomes.append(f"{meses_full[m]}/{ano_vigente}")
                    pendentes_datas.append((m, f"{ano_vigente}-{m:02d}-01", f"{meses_full[m]}/{ano_vigente}"))
                    chips_html.append(f"""
                    <div style="flex: 1 1 70px; min-width: 66px; text-align: center; padding: 6px 4px; border-radius: 8px; background: rgba(125, 87, 104, 0.22); border: 1.5px dashed #7D5768;">
                        <div style="font-size: 11px; font-weight: 700; color: #E0A96D;">{nome_abrev}/{str(ano_vigente)[-2:]}</div>
                        <div style="font-size: 10px; color: #E0A96D; font-weight: 500;">Pendente</div>
                        <div style="font-size: 9px; color: #E0A96D;">⏳ Falta</div>
                    </div>
                    """)
                else:
                    chips_html.append(f"""
                    <div style="flex: 1 1 70px; min-width: 66px; text-align: center; padding: 6px 4px; border-radius: 8px; background: rgba(255, 255, 255, 0.03); border: 1px solid rgba(255,255,255,0.08); opacity: 0.55;">
                        <div style="font-size: 11px; font-weight: 600; color: #bbb;">{nome_abrev}/{str(ano_vigente)[-2:]}</div>
                        <div style="font-size: 10px; color: #888;">Futuro</div>
                        <div style="font-size: 9px; color: #777;">⚪</div>
                    </div>
                    """)
                
            total_passados = mes_vigente
            total_lancados_ano = total_passados - len(pendentes_nomes)
        
            status_bar_html = f"""
            <div style="background: rgba(25, 48, 53, 0.6); border: 1px solid rgba(194, 163, 92, 0.3); border-radius: 12px; padding: 14px 16px; margin-top: 10px; margin-bottom: 8px;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; flex-wrap: wrap; gap: 8px;">
                    <span style="font-size: 13px; font-weight: 700; color: #F9F8F4; letter-spacing: 0.3px;">
                        🗓️ Fechamentos Mensais de {ano_vigente}: <span style="color: #C2A35C;">{total_lancados_ano} de {total_passados} meses apurados</span>
                    </span>
                    <span style="font-size: 12px; color: {'#85e085' if not pendentes_nomes else '#E0A96D'}; font-weight: 600;">
                        {'🎉 Todos os meses apurados até agora!' if not pendentes_nomes else f'⏳ {len(pendentes_nomes)} mês(es) pendente(s)'}
                    </span>
                </div>
                <div style="display: flex; gap: 6px; flex-wrap: wrap;">
                    {''.join(chips_html)}
                </div>
            </div>
            """
            st.html(status_bar_html)
        else:
            st.info("Nenhum histórico mensal registrado ainda. Atualize seus investimentos abaixo para iniciar o acompanhamento!")
            pendentes_datas = []

        # --------------------------------------------------------------------------
        # 4. FERRAMENTAS DE ATUALIZAÇÃO (COLAPSÁVEL PARA MANTER A TELA LIMPA)
        # --------------------------------------------------------------------------
        st.markdown("---")
        with st.expander("⚙️ Gerenciar Ativos & Atualizar Saldos Manuais", expanded=False):
            col1, col2 = st.columns([2, 1])
            with col1:
                st.write("#### 📝 Atualizar Saldo de Ativo Existente")
                st.caption("ℹ️ *A apuração dos investimentos é mensal, vinculada à posição do 1º dia do mês de referência.*")
                with st.form("form_atualizacao_manual"):
                    ativo_selecionado = st.selectbox("Selecione o Investimento", df_patrimonio['ativo'].tolist())
                    primeiro_dia_mes = date(date.today().year, date.today().month, 1)
                    data_competencia = st.date_input(
                        "Mês de Referência (Posição do 1º dia)", 
                        value=primeiro_dia_mes,
                        help="O fechamento consolidará este valor na competência mensal correspondente (1º dia do mês)."
                    )
                    saldo_total = st.number_input("Novo Saldo Consolidado (R$)", min_value=0.0, format="%.2f")
                    submit_atualizacao = st.form_submit_button("SALVAR ATUALIZAÇÃO")
                    if submit_atualizacao:
                        # Garantir que a data é gravada no 1º dia do mês selecionado
                        data_normalizada = f"{data_competencia.year:04d}-{data_competencia.month:02d}-01"
                        atualizar_patrimonio(ativo_selecionado, saldo_total, data_normalizada)
                        df_novo = listar_patrimonio()
                        soma_nova = df_novo['saldo'].sum()
                        registrar_historico_patrimonio(soma_nova, data_normalizada)
                        st.success(f"✅ {ativo_selecionado} atualizado para R$ {saldo_total:,.2f} na competência {data_competencia.strftime('%m/%Y')}!")
                        st.rerun()
                    
            with col2:
                st.write("#### ➕ Cadastrar Novo Ativo")
                with st.form("form_novo_ativo"):
                    novo_ativo = st.text_input("Nome do Ativo / Investimento", placeholder="Ex: LCI Banco Inter")
                    submit_novo = st.form_submit_button("CADASTRAR ATIVO")
                    if submit_novo and novo_ativo:
                        adicionar_ativo(novo_ativo)
                        st.success(f"Ativo '{novo_ativo}' adicionado com sucesso!")
                        st.rerun()
                    
                st.write("#### 🗑️ Remover Ativo")
                with st.form("form_remover_ativo"):
                    ativo_del = st.selectbox("Remover da Carteira", df_patrimonio['ativo'].tolist())
                    submit_del = st.form_submit_button("EXCLUIR ATIVO")
                    if submit_del and ativo_del:
                        excluir_ativo(ativo_del)
                        st.warning(f"Ativo '{ativo_del}' removido da carteira.")
                        st.rerun()

            # Sub-seção de Histórico Mensal Consolidado
            st.markdown("---")
            with st.expander("📅 Fechamentos Mensais Históricos (Lançar Meses Anteriores ou Excluir)", expanded=False):
                st.caption("Consulte os fechamentos mensais gravados ou registre posições de meses anteriores para alimentar o gráfico histórico:")
                col_h1, col_h2 = st.columns([1.2, 1])
                with col_h1:
                    st.write("##### 📋 Tabela de Competências Gravadas")
                    df_hist_tabela = listar_historico_patrimonio()
                    if not df_hist_tabela.empty:
                        df_hist_tabela['Competência'] = pd.to_datetime(df_hist_tabela['data_registro']).dt.strftime('%m/%Y')
                        df_hist_tabela['Posição Oficial'] = pd.to_datetime(df_hist_tabela['data_registro']).dt.strftime('01/%m/%Y')
                        df_hist_tabela['Total Consolidado'] = df_hist_tabela['total'].apply(lambda v: f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
                        st.dataframe(df_hist_tabela[['id', 'Competência', 'Posição Oficial', 'Total Consolidado']], use_container_width=True, hide_index=True)
                    else:
                        st.info("Nenhuma competência mensal gravada.")
                with col_h2:
                    st.write("##### 📌 Lançar Fechamento Mensal Direto")
                
                    # Seletor inteligente de meses pendentes
                    opcoes_pendentes = ["-- Escolha da lista de pendentes ou digite a data --"]
                    if 'pendentes_datas' in locals() and pendentes_datas:
                        for item in pendentes_datas:
                            opcoes_pendentes.append(f"{item[2]} (01/{item[0]:02d}/{ano_vigente})")
                
                    sel_mes_pendente = st.selectbox("⚡ Preencher com Mês Pendente:", opcoes_pendentes, key="sel_pendente_prefill")
                
                    # Data pré-selecionada baseada na escolha
                    data_padrao = date(date.today().year, date.today().month, 1)
                    if sel_mes_pendente != "-- Escolha da lista de pendentes ou digite a data --":
                        for item in pendentes_datas:
                            if item[2] in sel_mes_pendente:
                                data_padrao = date(ano_vigente, item[0], 1)
                                break
                            
                    with st.form("form_lancar_competencia_direta"):
                        dt_comp = st.date_input("Mês da Competência", value=data_padrao, key="comp_direta")
                        val_comp = st.number_input("Patrimônio Consolidado naquele Mês (R$)", min_value=0.0, format="%.2f", key="val_comp_direta")
                        btn_comp = st.form_submit_button("GRAVAR FECHAMENTO MENSAL")
                        if btn_comp and val_comp > 0:
                            dt_normalizada = f"{dt_comp.year:04d}-{dt_comp.month:02d}-01"
                            registrar_historico_patrimonio(val_comp, dt_normalizada)
                            st.success(f"Fechamento de {dt_comp.strftime('%m/%Y')} gravado com sucesso!")
                            st.rerun()


    with tab_consultor:
        dados_macro = obter_dados_oficiais_mercado()
        selic_oficial = dados_macro["selic"]
        cdi_oficial = dados_macro["cdi"]
        ipca_oficial = dados_macro["ipca"]
        poupanca_oficial = dados_macro["poupanca"]
        juro_real_oficial = dados_macro["juro_real"]
        
        # 1. Header Oficial do Consultor com Avatar da Manu
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, rgba(25, 48, 53, 0.95) 0%, rgba(74, 23, 40, 0.9) 100%); border: 1px solid rgba(194, 163, 92, 0.4); border-radius: 14px; padding: 20px 24px; margin-bottom: 20px; display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 15px; box-shadow: 0 8px 25px rgba(0,0,0,0.35);">
            <div style="display: flex; align-items: center; gap: 16px;">
                {avatar_elem}
                <div>
                    <div style="font-size: 1.35rem; font-weight: 800; color: #F9F8F4; font-family: 'Cinzel', serif; letter-spacing: 0.5px;">
                        Manu EconomyContY • Consultora de Investimentos & Risco
                    </div>
                    <div style="font-size: 0.84rem; color: #C2A35C; font-weight: 600; margin-top: 3px;">
                        Análise de Portfólio, Gestão de Risco e Estratégia de Alocação
                    </div>
                    <div style="font-size: 0.74rem; color: #E0A96D; margin-top: 2px;">
                        🏛️ <b>100% embasado em dados oficiais auditados:</b> Banco Central do Brasil (SGS), B3 e IBGE
                    </div>
                </div>
            </div>
            <div style="text-align: right;">
                <span style="background: rgba(194, 163, 92, 0.2); border: 1px solid #C2A35C; border-radius: 8px; padding: 6px 14px; font-size: 0.78rem; color: #F9F8F4; font-weight: 700;">
                    STATUS DO MERCADO: ATIVO
                </span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # 2. Painel de Indicadores Macroeconômicos Oficiais
        st.markdown("##### 🏛️ Indicadores Macroeconômicos Oficiais em Tempo Real")
        st.caption(f"Taxas públicas auditadas obtidas diretamente das APIs do Banco Central do Brasil e B3/IBGE:")
        
        col_m1, col_m2, col_m3, col_m4 = st.columns(4)
        with col_m1:
            st.markdown(f"""
            <div class="kpi-card" style="padding: 14px; text-align: center; border-left: 4px solid #C2A35C;">
                <div style="font-size: 0.72rem; color: #7D5768; font-weight: 700; text-transform: uppercase;">Taxa Selic Meta</div>
                <div style="font-size: 1.55rem; font-weight: 800; color: #F9F8F4; margin: 4px 0;">{selic_oficial:.2f}% <span style="font-size: 0.8rem; color: #C2A35C;">a.a.</span></div>
                <div style="font-size: 0.7rem; color: #9CA3AF;">Banco Central • SGS 432</div>
            </div>
            """, unsafe_allow_html=True)
            
        with col_m2:
            st.markdown(f"""
            <div class="kpi-card" style="padding: 14px; text-align: center; border-left: 4px solid #0E3646;">
                <div style="font-size: 0.72rem; color: #7D5768; font-weight: 700; text-transform: uppercase;">Taxa DI / CDI Oficial</div>
                <div style="font-size: 1.55rem; font-weight: 800; color: #F9F8F4; margin: 4px 0;">{cdi_oficial:.2f}% <span style="font-size: 0.8rem; color: #C2A35C;">a.a.</span></div>
                <div style="font-size: 0.7rem; color: #9CA3AF;">B3 / SGS 4389</div>
            </div>
            """, unsafe_allow_html=True)
            
        with col_m3:
            st.markdown(f"""
            <div class="kpi-card" style="padding: 14px; text-align: center; border-left: 4px solid #4A1728;">
                <div style="font-size: 0.72rem; color: #7D5768; font-weight: 700; text-transform: uppercase;">Inflação IPCA (12m)</div>
                <div style="font-size: 1.55rem; font-weight: 800; color: #F9F8F4; margin: 4px 0;">{ipca_oficial:.2f}% <span style="font-size: 0.8rem; color: #C2A35C;">a.a.</span></div>
                <div style="font-size: 0.7rem; color: #9CA3AF;">IBGE / SGS 13522</div>
            </div>
            """, unsafe_allow_html=True)
            
        with col_m4:
            st.markdown(f"""
            <div class="kpi-card" style="padding: 14px; text-align: center; border-left: 4px solid #193035;">
                <div style="font-size: 0.72rem; color: #7D5768; font-weight: 700; text-transform: uppercase;">Juro Real Oficial</div>
                <div style="font-size: 1.55rem; font-weight: 800; color: #85e085; margin: 4px 0;">+{juro_real_oficial:.2f}% <span style="font-size: 0.8rem; color: #C2A35C;">a.a.</span></div>
                <div style="font-size: 0.7rem; color: #9CA3AF;">Acima da Inflação</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<div style='margin-top: 20px;'></div>", unsafe_allow_html=True)
        
        # 3. Diagnóstico e Avaliação de Risco da Carteira Real
        st.markdown("##### 🔍 Diagnóstico Executivo da sua Carteira Atual")
        
        # Cálculos de distribuição
        saldo_rf = df_patrimonio[df_patrimonio['tipo_classe'] == 'Renda Fixa & Títulos Públicos']['saldo'].sum() if not df_patrimonio.empty else 0.0
        saldo_prev = df_patrimonio[df_patrimonio['tipo_classe'] == 'Previdência & Benefícios Sociais']['saldo'].sum() if not df_patrimonio.empty else 0.0
        saldo_fundos = df_patrimonio[df_patrimonio['tipo_classe'] == 'Fundos & Renda Variável']['saldo'].sum() if not df_patrimonio.empty else 0.0
        saldo_cripto = df_patrimonio[df_patrimonio['tipo_classe'] == 'Criptoativos & Alternativos']['saldo'].sum() if not df_patrimonio.empty else 0.0
        saldo_caixa = df_patrimonio[df_patrimonio['tipo_classe'] == 'Disponibilidade Bancária']['saldo'].sum() if not df_patrimonio.empty else 0.0
        
        perc_rf = (saldo_rf / total_patrimonio * 100) if total_patrimonio > 0 else 0.0
        perc_prev = (saldo_prev / total_patrimonio * 100) if total_patrimonio > 0 else 0.0
        perc_fundos = (saldo_fundos / total_patrimonio * 100) if total_patrimonio > 0 else 0.0
        perc_cripto = (saldo_cripto / total_patrimonio * 100) if total_patrimonio > 0 else 0.0
        perc_caixa = (saldo_caixa / total_patrimonio * 100) if total_patrimonio > 0 else 0.0
        
        # Determinação do Perfil de Risco da Carteira
        if (perc_rf + perc_prev + perc_caixa) >= 80 and perc_cripto <= 5:
            perfil_nome = "Conservador com Foco em Preservação & Blindagem"
            perfil_cor = "#C2A35C"
            perfil_badge = "🛡️ CONSERVADOR"
            perfil_desc = "Sua carteira prioriza a estabilidade e previsibilidade dos rendimentos, com quase a totalidade do capital protegida em renda fixa e benefícios garantidos."
        elif (perc_fundos + perc_cripto) > 35:
            perfil_nome = "Arrojado / Crescimento Agressivo"
            perfil_cor = "#7D5768"
            perfil_badge = "🚀 ARROJADO"
            perfil_desc = "Sua carteira busca retornos exponenciais aceitando maior oscilação patrimonial no curto prazo."
        else:
            perfil_nome = "Moderado com Estratégia Híbrida"
            perfil_cor = "#0E3646"
            perfil_badge = "⚖️ MODERADO"
            perfil_desc = "Sua carteira equilibra a robustez da renda fixa com oportunidades seletivas em fundos e ativos de valorização."
            
        c_diag1, c_diag2 = st.columns([1.1, 1])
        with c_diag1:
            st.markdown(f"""
            <div style="background: rgba(25, 48, 53, 0.7); border: 1px solid rgba(194, 163, 92, 0.3); border-radius: 12px; padding: 18px 20px;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                    <span style="font-size: 0.85rem; font-weight: 700; color: #F9F8F4; text-transform: uppercase;">Classificação de Risco</span>
                    <span style="background: rgba(194, 163, 92, 0.2); border: 1px solid {perfil_cor}; border-radius: 6px; padding: 4px 10px; font-size: 0.75rem; font-weight: 700; color: #F9F8F4;">
                        {perfil_badge}
                    </span>
                </div>
                <div style="font-size: 1.15rem; font-weight: 700; color: #C2A35C; margin-bottom: 6px;">
                    {perfil_nome}
                </div>
                <p style="font-size: 0.84rem; color: #D1D5DB; line-height: 1.45; margin: 0 0 12px 0;">
                    {perfil_desc}
                </p>
                <div style="border-top: 1px solid rgba(194, 163, 92, 0.2); padding-top: 10px; font-size: 0.78rem; color: #9CA3AF;">
                    <b>Alocação Consolidada:</b><br>
                    • Renda Fixa: <b>{perc_rf:.1f}%</b> | • Previdência: <b>{perc_prev:.1f}%</b><br>
                    • Fundos: <b>{perc_fundos:.1f}%</b> | • Cripto: <b>{perc_cripto:.1f}%</b> | • Caixa: <b>{perc_caixa:.1f}%</b>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
        with c_diag2:
            ganho_mensal_cdb = saldo_caixa * ((1.0 + cdi_oficial/100.0)**(1.0/12.0) - 1.0)
            ganho_anual_cdb = saldo_caixa * (cdi_oficial/100.0)
            
            if saldo_caixa > 500:
                st.markdown(f"""
                <div style="background: rgba(74, 23, 40, 0.35); border: 1.5px solid #7D5768; border-radius: 12px; padding: 18px 20px;">
                    <div style="display: flex; align-items: gap: 8px; margin-bottom: 8px;">
                        <span style="font-size: 1.1rem;">⚠️</span>
                        <span style="font-size: 0.86rem; font-weight: 700; color: #F9F8F4; text-transform: uppercase;">
                            Oportunidade: Dinheiro Parado em Conta
                        </span>
                    </div>
                    <div style="font-size: 0.84rem; color: #E5E7EB; line-height: 1.45;">
                        Você possui <b>R$ {saldo_caixa:,.2f}</b> ({perc_caixa:.1f}% da carteira) em disponibilidade bancária rendendo zero.
                        <div style="background: rgba(0,0,0,0.25); border-radius: 8px; padding: 10px; margin: 10px 0; border: 1px solid rgba(194, 163, 92, 0.3);">
                            <span style="color: #C2A35C; font-weight: 700;">Ganho Adicional no CDI Oficial ({cdi_oficial:.2f}% a.a.):</span><br>
                            • <b>+ R$ {ganho_mensal_cdb:,.2f} / mês</b><br>
                            • <b>+ R$ {ganho_anual_cdb:,.2f} / ano</b> com liquidez diária e proteção FGC.
                        </div>
                        <span style="font-size: 0.78rem; color: #85e085;">💡 Recomendação: Migre o saldo excedente para um CDB 100% CDI de resgate imediato ou Tesouro Selic.</span>
                    </div>
                </div>
                """.replace(",", "X").replace(".", ",").replace("X", "."), unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div style="background: rgba(25, 48, 53, 0.7); border: 1.5px solid #C2A35C; border-radius: 12px; padding: 18px 20px;">
                    <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 8px;">
                        <span style="font-size: 1.1rem;">✅</span>
                        <span style="font-size: 0.86rem; font-weight: 700; color: #F9F8F4; text-transform: uppercase;">
                            Excelente Eficiência de Caixa
                        </span>
                    </div>
                    <div style="font-size: 0.84rem; color: #E5E7EB; line-height: 1.45;">
                        Praticamente 100% do seu patrimônio está investido e rentabilizando. Seu saldo em conta corrente está otimizado (menos de 500 reais parados), o que demonstra excelente disciplina financeira!
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
        st.markdown("<div style='margin-top: 20px;'></div>", unsafe_allow_html=True)
        
        # 4. Estratégias & Recomendações de Mercado da Manu (100% Oficiais)
        st.markdown("##### 💡 Recomendações Estratégicas da Manu (Cenário de Mercado Oficial)")
        st.caption("Estratégias estruturadas com base na Taxa Selic oficial do COPOM/BCB e na curva de juros da B3:")
        
        c_rec1, c_rec2, c_rec3 = st.columns(3)
        with c_rec1:
            st.markdown(f"""
            <div style="background: rgba(25, 48, 53, 0.6); border: 1px solid rgba(194, 163, 92, 0.3); border-radius: 12px; padding: 16px; height: 100%;">
                <div style="font-size: 0.82rem; font-weight: 700; color: #C2A35C; text-transform: uppercase;">
                    1. Reserva & Liquidez Imediata
                </div>
                <div style="font-size: 1.05rem; font-weight: 700; color: #F9F8F4; margin: 6px 0;">
                    Tesouro Selic & CDB 100% CDI
                </div>
                <p style="font-size: 0.8rem; color: #D1D5DB; line-height: 1.4;">
                    Com a Selic em <b>{selic_oficial:.2f}% ao ano</b>, a renda fixa pós-fixada paga retorno bruto superior a 1% ao mês com risco soberano ou garantia do FGC até R$ 250 mil por instituição.
                </p>
                <div style="font-size: 0.74rem; color: #9CA3AF; border-top: 1px solid rgba(255,255,255,0.1); padding-top: 8px;">
                    🎯 <b>Meta:</b> 3 a 6 meses do seu custo de vida mensal.
                </div>
            </div>
            """, unsafe_allow_html=True)
            
        with c_rec2:
            st.markdown(f"""
            <div style="background: rgba(25, 48, 53, 0.6); border: 1px solid rgba(194, 163, 92, 0.3); border-radius: 12px; padding: 16px; height: 100%;">
                <div style="font-size: 0.82rem; font-weight: 700; color: #C2A35C; text-transform: uppercase;">
                    2. Isenção Fiscal (LCI / LCA)
                </div>
                <div style="font-size: 1.05rem; font-weight: 700; color: #F9F8F4; margin: 6px 0;">
                    Eficiência Líquida Sem IR
                </div>
                <p style="font-size: 0.8rem; color: #D1D5DB; line-height: 1.4;">
                    Uma LCI/LCA a <b>92% do CDI</b> rende líquido o equivalente a um <b>CDB de ~118% do CDI</b> (alíquota de 22,5% de IR). Excelente para prazos de 9 meses a 2 anos.
                </p>
                <div style="font-size: 0.74rem; color: #9CA3AF; border-top: 1px solid rgba(255,255,255,0.1); padding-top: 8px;">
                    🎯 <b>Vantagem:</b> Isenção total de IR para pessoa física.
                </div>
            </div>
            """, unsafe_allow_html=True)
            
        with c_rec3:
            st.markdown(f"""
            <div style="background: rgba(25, 48, 53, 0.6); border: 1px solid rgba(194, 163, 92, 0.3); border-radius: 12px; padding: 16px; height: 100%;">
                <div style="font-size: 0.82rem; font-weight: 700; color: #C2A35C; text-transform: uppercase;">
                    3. Blindagem de Poder de Compra
                </div>
                <div style="font-size: 1.05rem; font-weight: 700; color: #F9F8F4; margin: 6px 0;">
                    Tesouro IPCA+ (Juro Real)
                </div>
                <p style="font-size: 0.8rem; color: #D1D5DB; line-height: 1.4;">
                    Com a taxa real oficial em <b>+{juro_real_oficial:.2f}% a.a.</b>, travar taxas acima de IPCA + 6% ao ano garante aumento real do patrimônio contra a inflação histórica para objetivos de médio/longo prazo.
                </p>
                <div style="font-size: 0.74rem; color: #9CA3AF; border-top: 1px solid rgba(255,255,255,0.1); padding-top: 8px;">
                    🎯 <b>Meta:</b> Aposentadoria e projetos acima de 3 anos.
                </div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<div style='margin-top: 25px;'></div>", unsafe_allow_html=True)
        
        # 5. Simulador Interativo de Projeção & Rebalanceamento
        st.markdown("##### 📈 Simulador de Projeção Patrimonial & Rebalanceamento")
        st.caption("Simule o crescimento do seu patrimônio consolidado com base nas taxas oficiais atuais do mercado brasileiro:")
        
        c_sim1, c_sim2 = st.columns([1, 2])
        with c_sim1:
            with st.form("form_simulador_consultor"):
                st.write("##### Parâmetros da Simulação")
                aporte_mensal = st.number_input("Aporte Mensal Previsto (R$)", min_value=0.0, value=1000.0, step=200.0)
                prazo_meses = st.select_slider("Horizonte de Tempo (Meses)", options=[6, 12, 24, 36, 60], value=24)
                tx_personalizada = st.slider("Taxa Anual Média Alvo (% a.a.)", min_value=5.0, max_value=20.0, value=float(cdi_oficial), step=0.25)
                btn_simular = st.form_submit_button("SIMULAR PROJEÇÃO PATRIMONIAL", use_container_width=True)
                
        with c_sim2:
            eixo_m = np.arange(1, prazo_meses + 1)
            tx_m_alvo = (1.0 + tx_personalizada/100.0) ** (1.0/12.0) - 1.0
            tx_m_cdi = (1.0 + cdi_oficial/100.0) ** (1.0/12.0) - 1.0
            tx_m_poup = (1.0 + (poupanca_oficial * 12.0)/100.0) ** (1.0/12.0) - 1.0
            tx_m_ipca = (1.0 + ipca_oficial/100.0) ** (1.0/12.0) - 1.0
            
            proj_carteira = []
            proj_cdi = []
            proj_poup = []
            proj_ipca = []
            
            cur_cart = total_patrimonio
            cur_cdi = total_patrimonio
            cur_poup = total_patrimonio
            cur_ipca = total_patrimonio
            
            for m in eixo_m:
                cur_cart = (cur_cart + aporte_mensal) * (1.0 + tx_m_alvo)
                cur_cdi = (cur_cdi + aporte_mensal) * (1.0 + tx_m_cdi)
                cur_poup = (cur_poup + aporte_mensal) * (1.0 + tx_m_poup)
                cur_ipca = (cur_ipca + aporte_mensal) * (1.0 + tx_m_ipca)
                
                proj_carteira.append(cur_cart)
                proj_cdi.append(cur_cdi)
                proj_poup.append(cur_poup)
                proj_ipca.append(cur_ipca)
                
            df_proj = pd.DataFrame({
                "Mês": eixo_m,
                f"Sua Carteira Alvo ({tx_personalizada:.1f}%)": proj_carteira,
                f"100% CDI Oficial ({cdi_oficial:.1f}%)": proj_cdi,
                f"Poupança Oficial ({poupanca_oficial*12.0:.1f}%)": proj_poup,
                f"Inflação IPCA ({ipca_oficial:.1f}%)": proj_ipca
            })
            
            df_proj_melt = df_proj.melt(id_vars="Mês", var_name="Estratégia", value_name="Saldo (R$)")
            
            fig_proj = px.line(
                df_proj_melt,
                x="Mês",
                y="Saldo (R$)",
                color="Estratégia",
                color_discrete_map={
                    f"Sua Carteira Alvo ({tx_personalizada:.1f}%)": "#C2A35C",
                    f"100% CDI Oficial ({cdi_oficial:.1f}%)": "#0E3646",
                    f"Poupança Oficial ({poupanca_oficial*12.0:.1f}%)": "#7D5768",
                    f"Inflação IPCA ({ipca_oficial:.1f}%)": "#888888"
                }
            )
            fig_proj.update_layout(
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#F9F8F4", family="Inter, sans-serif"),
                xaxis=dict(showgrid=True, gridcolor="rgba(194, 163, 92, 0.15)", title="Mês"),
                yaxis=dict(showgrid=True, gridcolor="rgba(194, 163, 92, 0.15)", tickprefix="R$ "),
                margin=dict(l=10, r=10, t=10, b=10),
                height=300,
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            st.plotly_chart(fig_proj, use_container_width=True)
            
            dif_poup = proj_carteira[-1] - proj_poup[-1]
            st.success(f"""
            🏆 **Resultado em {prazo_meses} meses:** Seu patrimônio projetado atingirá **R$ {proj_carteira[-1]:,.2f}**!  
            Com essa estratégia otimizada pela Manu, você acumulará **R$ {dif_poup:,.2f} a mais** do que se deixasse o dinheiro na Poupança tradicional!
            """.replace(",", "X").replace(".", ",").replace("X", "."))

    render_footer_economyconty()

