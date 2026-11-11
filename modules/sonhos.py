import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date
import database
from utils import render_footer_economyconty

def render_sonhos(user_id, nome_usuario="", manu_face_b64=""):
    ICONES_SONHOS = database.ICONES_SONHOS

    def listar_sonhos():
        return database.listar_sonhos(user_id)

    def listar_patrimonio():
        return database.listar_patrimonio(user_id)

    def criar_sonho(titulo, icone, valor_alvo, valor_inicial=0.0, ativo_vinculado="", aporte_mensal_planejado=0.0, data_limite="", criar_caixinha_patrimonio=True):
        return database.criar_sonho(
            user_id=user_id,
            titulo=titulo,
            icone=icone,
            valor_alvo=valor_alvo,
            valor_inicial=valor_inicial,
            ativo_vinculado=ativo_vinculado,
            aporte_mensal_planejado=aporte_mensal_planejado,
            data_limite=data_limite,
            criar_caixinha_patrimonio=criar_caixinha_patrimonio
        )

    def aportar_sonho(id_sonho, valor_aporte, registrar_lancamento=True, banco="Itaú", data_aporte=None):
        return database.aportar_sonho(
            user_id=user_id,
            id_sonho=id_sonho,
            valor_aporte=valor_aporte,
            registrar_lancamento=registrar_lancamento,
            banco=banco,
            data_aporte=data_aporte
        )

    def excluir_sonho(id_sonho):
        return database.excluir_sonho(user_id, id_sonho)

    avatar_elem = f'<img src="data:image/png;base64,{manu_face_b64}" style="width: 50px; height: 50px; border-radius: 50%; border: 2px solid #C2A35C; object-fit: cover; box-shadow: 0 0 10px rgba(194,163,92,0.35);" />' if manu_face_b64 else '<div style="width: 50px; height: 50px; border-radius: 50%; background: #C2A35C; color: #193035; display: flex; align-items: center; justify-content: center; font-weight: 700;">EC</div>'

    st.markdown(f"""
        <div style='background: linear-gradient(135deg, rgba(25, 48, 53, 0.92) 0%, rgba(14, 54, 70, 0.95) 100%); border: 1px solid rgba(194, 163, 92, 0.35); border-left: 5px solid #C2A35C; padding: 14px 20px; border-radius: 12px; margin-bottom: 18px; display: flex; align-items: center; gap: 16px; box-shadow: 0 8px 25px rgba(0,0,0,0.3);'>
            {avatar_elem}
            <div>
                <div style="font-size: 0.72rem; color: #C2A35C; font-weight: 700; text-transform: uppercase; letter-spacing: 0.08em;">Planejamento Futuro & Caixinhas • EconomyContY</div>
                <div style="color: #F9F8F4; font-size: 0.9rem; margin-top: 2px;">
                    Olá, <b>{nome_usuario or 'Investidor'}</b>! Transforme cada objetivo em uma <b>Caixinha conectada ao seu Patrimônio</b> e acompanhe exatamente quantos <b>% faltam</b> a cada novo aporte!
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)

    st.markdown("<h2>🎯 Sonhos & Caixinhas (Planejamento Futuro)</h2>", unsafe_allow_html=True)
    st.caption("Crie metas como **Comprar uma TV Nova, Trocar de Carro ou Comprar uma Casa**, vincule cada sonho a uma **Caixinha em Meu Patrimônio** e receba alertas imediatos de quanto **% falta** a cada aplicação.")

    df_sonhos = listar_sonhos()
    df_pat_sonhos = listar_patrimonio()
    lista_ativos_pat = df_pat_sonhos['ativo'].tolist() if not df_pat_sonhos.empty else []

    total_alvo_sonhos = float(df_sonhos['valor_alvo'].sum()) if not df_sonhos.empty else 0.0
    total_acumulado_sonhos = float(df_sonhos['valor_atual'].sum()) if not df_sonhos.empty else 0.0
    total_falta_sonhos = max(total_alvo_sonhos - total_acumulado_sonhos, 0.0)
    pct_geral_atingido = min((total_acumulado_sonhos / total_alvo_sonhos) * 100.0, 100.0) if total_alvo_sonhos > 0 else 0.0
    pct_geral_falta = max(100.0 - pct_geral_atingido, 0.0) if total_alvo_sonhos > 0 else 100.0

    ks1, ks2, ks3, ks4 = st.columns(4)
    ks1.metric("🎯 Total Planejado nos Sonhos", f"R$ {total_alvo_sonhos:,.2f}", f"{len(df_sonhos)} sonho(s) ativo(s)")
    ks2.metric("💰 Total Já Guardado (Caixinhas)", f"R$ {total_acumulado_sonhos:,.2f}", f"{pct_geral_atingido:.1f}% conquistado")
    ks3.metric("⏳ Falta Acumular (R$)", f"R$ {total_falta_sonhos:,.2f}", f"Faltam {pct_geral_falta:.1f}% do total", delta_color="off")
    concluidos_cnt = int((df_sonhos['valor_atual'] >= df_sonhos['valor_alvo']).sum()) if not df_sonhos.empty else 0
    ks4.metric("🏆 Sonhos Realizados (100%)", f"{concluidos_cnt} de {len(df_sonhos)}", "Vinculados ao Patrimônio")

    st.markdown("<div style='margin-top:12px;'></div>", unsafe_allow_html=True)

    col_act1, col_act2 = st.columns([1.3, 2.7])
    with col_act1:
        with st.popover("✨ + Criar Novo Sonho / Caixinha", use_container_width=True):
            st.markdown("#### 🎯 Configurar Novo Sonho")
            s_icone = st.selectbox("Categoria do Sonho:", ICONES_SONHOS, key="novo_sonho_icone")
            sugestao_nome = s_icone.split(" ", 1)[-1].split("/")[0].strip()
            s_titulo = st.text_input("Nome do Sonho / Objetivo:", placeholder=f"Ex: {sugestao_nome} (LG OLED 65, SUV, Casa...)", key="novo_sonho_titulo")
            sc1, sc2 = st.columns(2)
            with sc1:
                s_alvo = st.number_input("Valor do Sonho (Meta R$):", min_value=10.0, value=5000.0, step=500.0, format="%.2f", key="novo_sonho_alvo")
            with sc2:
                s_inicial = st.number_input("Saldo Já Guardado (R$):", min_value=0.0, value=0.0, step=100.0, format="%.2f", key="novo_sonho_ini")
            sc3, sc4 = st.columns(2)
            with sc3:
                s_aporte_mes = st.number_input("Aporte Mensal Planejado (R$):", min_value=0.0, value=500.0, step=100.0, format="%.2f", key="novo_sonho_ap_mes")
            with sc4:
                s_data_lim = st.date_input("Meta de Data (Opcional):", value=date(date.today().year + 1, date.today().month, 1), key="novo_sonho_dt")

            opcoes_vinculo = ["✨ Criar Nova Caixinha no Patrimônio"] + lista_ativos_pat + ["Não vincular"]
            s_vinculo = st.selectbox(
                "Ligação com Investimentos (💼 Meu Patrimônio):",
                opcoes_vinculo,
                help="Cria automaticamente um ativo 'Caixinha: Nome do Sonho' na aba Meu Patrimônio ou conecta a um investimento já existente.",
                key="novo_sonho_vinc"
            )
            if st.button("🚀 Criar Sonho e Conectar Caixinha", type="primary", use_container_width=True, key="btn_criar_sonho"):
                nome_final_s = s_titulo.strip() if s_titulo.strip() else sugestao_nome
                criar_sonho(
                    titulo=nome_final_s,
                    icone=s_icone,
                    valor_alvo=s_alvo,
                    valor_inicial=s_inicial,
                    ativo_vinculado=s_vinculo,
                    aporte_mensal_planejado=s_aporte_mes,
                    data_limite=s_data_lim.strftime("%Y-%m-%d"),
                    criar_caixinha_patrimonio=(s_vinculo == "✨ Criar Nova Caixinha no Patrimônio")
                )
                pct_ini = min((s_inicial / max(s_alvo, 0.01)) * 100.0, 100.0)
                pct_falta_ini = max(100.0 - pct_ini, 0.0)
                st.toast(f"🎯 Sonho '{nome_final_s}' criado! Falta {pct_falta_ini:.1f}% para atingir sua meta.")
                st.rerun()

    with col_act2:
        st.info("💡 **Como funciona a ligação com Investimentos:** Cada sonho possui sua **Caixinha** sincronizada com a aba **💼 Meu Patrimônio**. Você pode aplicar direto no card abaixo ou ao registrar qualquer lançamento em `📈 Aportes & Patrimônio`.")

    st.markdown("---")

    if df_sonhos.empty:
        st.markdown("""
        <div style="background: rgba(14, 54, 70, 0.45); border: 1px dashed rgba(212, 175, 55, 0.45); border-radius: 14px; padding: 26px; text-align: center; margin: 12px 0;">
            <h4 style="margin:0 0 8px 0; color:#FFDE7A;">✨ Você ainda não cadastrou nenhum Sonho ou Caixinha</h4>
            <p style="color:#E2EEF0; font-size:0.92rem; margin:0;">Clique em <b>"✨ + Criar Novo Sonho / Caixinha"</b> acima ou escolha um modelo rápido abaixo para começar (ex: 📺 TV Nova, 🚗 Carro, 🏠 Casa Própria).</p>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("##### ⚡ Modelos Rápidos em 1 Clique:")
        cm1, cm2, cm3 = st.columns(3)
        with cm1:
            if st.button("📺 Criar Meta: Comprar TV Nova (R$ 4.500)", use_container_width=True, key="tpl_tv"):
                criar_sonho("Comprar TV Nova 65\"", "📺 TV Nova / Eletrônicos", 4500.0, 0.0, "✨ Criar Nova Caixinha no Patrimônio", 450.0, f"{date.today().year}-12-31", True)
                st.rerun()
        with cm2:
            if st.button("🚗 Criar Meta: Comprar um Carro (R$ 65.000)", use_container_width=True, key="tpl_carro"):
                criar_sonho("Comprar Carro Novo", "🚗 Carro / Moto Nova", 65000.0, 0.0, "✨ Criar Nova Caixinha no Patrimônio", 1500.0, f"{date.today().year + 2}-12-31", True)
                st.rerun()
        with cm3:
            if st.button("🏠 Criar Meta: Comprar uma Casa (R$ 250.000)", use_container_width=True, key="tpl_casa"):
                criar_sonho("Entrada / Compra da Casa Própria", "🏠 Casa Própria / Imóvel", 250000.0, 0.0, "✨ Criar Nova Caixinha no Patrimônio", 2500.0, f"{date.today().year + 4}-12-31", True)
                st.rerun()
    else:
        cols_sonhos = st.columns(2)
        for idx_s, row_s in df_sonhos.iterrows():
            s_id = int(row_s['id'])
            s_tit = str(row_s['titulo'])
            s_ico = str(row_s['icone'])
            s_emoji = s_ico.split(" ")[0] if " " in s_ico else "🎯"
            s_alvo_v = max(float(row_s['valor_alvo']), 0.01)
            s_atual_v = float(row_s['valor_atual'])
            s_vinc = str(row_s['ativo_vinculado'] or "")
            s_ap_plan = float(row_s['aporte_mensal_planejado'] or 0.0)

            pct_done = min((s_atual_v / s_alvo_v) * 100.0, 100.0)
            pct_missing = max(100.0 - pct_done, 0.0)
            val_missing = max(s_alvo_v - s_atual_v, 0.0)

            if val_missing <= 0:
                est_texto = "🎉 Sonho 100% atingido! Parabéns pela conquista!"
                cor_barra = "#10B981"
                cor_borda = "rgba(16, 185, 129, 0.55)"
            else:
                cor_barra = "#D4AF37" if pct_done < 75 else "#10B981"
                cor_borda = "rgba(212, 175, 55, 0.4)"
                if s_ap_plan > 0:
                    taxa_m = 0.009
                    saldo_sim = s_atual_v
                    meses_sim = 0
                    while saldo_sim < s_alvo_v and meses_sim < 600:
                        saldo_sim = saldo_sim * (1 + taxa_m) + s_ap_plan
                        meses_sim += 1
                    anos_i = meses_sim // 12
                    meses_r = meses_sim % 12
                    tempo_str = f"{anos_i}a e {meses_r}m" if anos_i > 0 else f"{meses_r} mês(es)"
                    est_texto = f"⏱️ Mantendo R$ {s_ap_plan:,.2f}/mês (+CDI), você realiza em ~<b>{tempo_str}</b>"
                else:
                    est_texto = "💡 Faça aportes na caixinha para acelerar sua conquista"

            badge_vinc = f"🔗 Caixinha no Patrimônio: <b>{s_vinc}</b>" if s_vinc else "🔓 Sem ativo vinculado"

            with cols_sonhos[idx_s % 2]:
                st.markdown(f"""
                <div style="background: linear-gradient(145deg, rgba(14, 54, 70, 0.88), rgba(22, 37, 61, 0.92)); border: 1.5px solid {cor_borda}; border-radius: 14px; padding: 18px 20px; margin-bottom: 10px; box-shadow: 0 8px 20px rgba(0,0,0,0.28);">
                    <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:8px;">
                        <div>
                            <span style="font-size:0.75rem; color:#B5D5DC; text-transform:uppercase; letter-spacing:0.6px;">{s_ico}</span>
                            <h3 style="margin:2px 0 0 0; color:#F9F8F4; font-size:1.22rem;">{s_emoji} {s_tit}</h3>
                        </div>
                        <div style="text-align:right;">
                            <span style="background:rgba(212,175,55,0.18); border:1px solid #D4AF37; color:#FFDE7A; font-weight:800; font-size:0.84rem; padding:4px 10px; border-radius:20px;">
                                {f'Falta {pct_missing:.1f}%' if val_missing > 0 else '🏆 100% Concluído!'}
                            </span>
                        </div>
                    </div>
                    <div style="font-size:0.8rem; color:#B5D5DC; margin-bottom:10px;">{badge_vinc}</div>
                    <div style="background:rgba(4,20,24,0.75); border-radius:10px; height:14px; width:100%; overflow:hidden; margin-bottom:10px; border:1px solid rgba(255,255,255,0.08);">
                        <div style="background:linear-gradient(90deg, #B88A2D, {cor_barra}); width:{pct_done:.1f}%; height:100%; border-radius:10px; transition:width 0.4s ease;"></div>
                    </div>
                    <div style="display:flex; justify-content:space-between; font-size:0.86rem; color:#E2EEF0; margin-bottom:6px;">
                        <span>💰 Guardado: <b style="color:#34D399;">R$ {s_atual_v:,.2f}</b> ({pct_done:.1f}%)</span>
                        <span>🎯 Meta: <b style="color:#FFDE7A;">R$ {s_alvo_v:,.2f}</b></span>
                    </div>
                    <div style="display:flex; justify-content:space-between; font-size:0.82rem; color:#FCD34D; background:rgba(0,0,0,0.22); padding:6px 10px; border-radius:8px;">
                        <span>⏳ Falta guardar: <b>R$ {val_missing:,.2f} ({pct_missing:.1f}%)</b></span>
                    </div>
                    <div style="font-size:0.78rem; color:#B5D5DC; margin-top:8px;">{est_texto}</div>
                </div>
                """, unsafe_allow_html=True)

                b_col1, b_col2 = st.columns([2.2, 1])
                with b_col1:
                    with st.popover(f"💰 + Aplicar na Caixinha ({s_emoji} {s_tit[:18]})", use_container_width=True):
                        st.markdown(f"##### 💰 Novo Aporte • {s_emoji} {s_tit}")
                        st.caption(f"Ativo vinculado: **{s_vinc or 'Caixinha Própria'}**")
                        ap_val = st.number_input("Valor da Aplicação (R$):", min_value=1.0, value=float(s_ap_plan if s_ap_plan > 0 else 200.0), step=50.0, format="%.2f", key=f"ap_val_{s_id}")
                        ap_bco = st.text_input("Banco / Corretora de Origem:", value="Itaú", key=f"ap_bco_{s_id}")
                        ap_reg_ext = st.checkbox("Registrar também no Extrato (📈 Aportes & Patrimônio)", value=True, key=f"ap_reg_{s_id}")

                        novo_s_prev = s_atual_v + ap_val
                        pct_ating_prev = min((novo_s_prev / s_alvo_v) * 100.0, 100.0)
                        pct_falta_prev = max(100.0 - pct_ating_prev, 0.0)
                        val_falta_prev = max(s_alvo_v - novo_s_prev, 0.0)
                        st.markdown(
                            f"<div style='background:rgba(16,185,129,0.12); border:1px solid rgba(16,185,129,0.4); border-radius:8px; padding:8px 10px; font-size:0.82rem; color:#E2EEF0; margin-bottom:8px;'>"
                            f"📊 <b>Simulação do Aporte:</b> Seu saldo irá para <b>R$ {novo_s_prev:,.2f}</b> ({pct_ating_prev:.1f}%) e "
                            f"<b style='color:#FFDE7A;'>faltará apenas {pct_falta_prev:.1f}% (R$ {val_falta_prev:,.2f})</b> para realizar este sonho!"
                            f"</div>",
                            unsafe_allow_html=True
                        )

                        if st.button("✅ Confirmar Aplicação na Caixinha", type="primary", use_container_width=True, key=f"btn_conf_ap_{s_id}"):
                            info_res = aportar_sonho(
                                id_sonho=s_id,
                                valor_aporte=ap_val,
                                registrar_lancamento=ap_reg_ext,
                                banco=ap_bco.strip() or "Itaú",
                                data_aporte=date.today()
                            )
                            if info_res:
                                st.session_state["alerta_aporte_sonho"] = info_res
                                st.toast(
                                    f"🎯 +R$ {ap_val:,.2f} na Caixinha '{info_res['titulo']}'! "
                                    f"Atingido: {info_res['pct_atingido']:.1f}% | Falta apenas {info_res['pct_falta']:.1f}% (R$ {info_res['valor_falta']:,.2f})!"
                                )
                            st.rerun()
                with b_col2:
                    if st.button("🗑️ Excluir", key=f"del_sonho_{s_id}", use_container_width=True):
                        excluir_sonho(s_id)
                        st.toast(f"Sonho '{s_tit}' removido.")
                        st.rerun()

    render_footer_economyconty()
