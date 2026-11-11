from dateutil.relativedelta import relativedelta
import streamlit as st
import pandas as pd
import uuid
from datetime import datetime, date
import database
from ai_scanner import extrair_dados_recibo_ia
from utils import render_footer_economyconty
import io

def render_lancamentos(user_id, nome_usuario="", manu_face_b64=""):
    def listar_lancamentos():
        return database.listar_lancamentos(user_id)
    def inserir_lancamento(tipo, descricao, valor, data_vencimento, categoria="Geral", conta="Conta Principal", status="Realizado", protocolo=None, data_pagamento=None, tributavel=0, dedutivel=0, subcategoria=None, **kwargs):
        return database.inserir_lancamento(user_id, tipo, descricao, valor, data_vencimento, categoria=categoria, conta=conta, status=status, protocolo=protocolo, data_pagamento=data_pagamento, tributavel=tributavel, dedutivel=dedutivel, subcategoria=subcategoria, **kwargs)
    def adicionar_lancamento(tipo, descricao, valor, data_vencimento, categoria="Geral", conta="Conta Principal", status="Realizado", dedutivel=0, tributavel=0, origem="Manual", protocolo=None, data_pagamento=None, subcategoria=None, **kwargs):
        return database.adicionar_lancamento(user_id, tipo, descricao, valor, data_vencimento, categoria=categoria, conta=conta, status=status, dedutivel=dedutivel, tributavel=tributavel, origem=origem, protocolo=protocolo, data_pagamento=data_pagamento, subcategoria=subcategoria, **kwargs)
    SUBCATEGORIAS_DESPESAS = database.SUBCATEGORIAS_DESPESAS
    SUBCATEGORIAS_RECEITAS = database.SUBCATEGORIAS_RECEITAS
    MAPA_SUBCATEGORIA_503020 = database.MAPA_SUBCATEGORIA_503020
    inferir_subcategoria_icone = database.inferir_subcategoria_icone

    st.markdown('''
    <div style="margin-bottom: 1.5rem; padding-bottom: 0.8rem; border-bottom: 1px solid rgba(212, 175, 55, 0.2);">
        <h1 style="margin: 0; font-size: 2rem; font-weight: 800; background: linear-gradient(90deg, #F9FAFB, #D4AF37); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
            ✍️ Lançamentos Financeiros & Scanner IA
        </h1>
        <p style="margin: 4px 0 0 0; color: #E2EEF0; font-size: 0.95rem; font-weight: 500;">Capture notas fiscais com IA, registre receitas/despesas em lote ou importe extratos bancários</p>
    </div>
    ''', unsafe_allow_html=True)

    tab_ia, tab_manual, tab_csv = st.tabs(["📸 Scanner de Cupom com IA", "📝 Novo Lançamento Manual & Lote", "📂 Importar via CSV / Extrato"])

    with tab_ia:
        manu_scanner_face = f'<img src="data:image/png;base64,{manu_face_b64}" style="width: 50px; height: 50px; border-radius: 50%; border: 2px solid #C2A35C; object-fit: cover; box-shadow: 0 0 8px rgba(194,163,92,0.35);" />' if manu_face_b64 else ''
        st.markdown(f'''
            <div style='background: linear-gradient(135deg, rgba(25, 48, 53, 0.85) 0%, rgba(14, 54, 70, 0.9) 100%); border: 1px solid rgba(194, 163, 92, 0.3); border-left: 4px solid #C2A35C; padding: 12px 18px; border-radius: 12px; margin-bottom: 20px; display: flex; align-items: center; gap: 14px;'>
                {manu_scanner_face}
                <div>
                    <div style="font-weight: 700; color: #F9F8F4; font-size: 0.95rem;">📸 Scanner Inteligente da Manu</div>
                    <div style="color: #F9F8F4; font-size: 0.84rem; margin-top: 2px;">
                        Aponte a câmera do seu celular para o cupom ou envie uma foto. A <b>Manu</b> lerá o valor, data, estabelecimento e sugerirá a categoria para você revisar e salvar!
                    </div>
                </div>
            </div>
        ''', unsafe_allow_html=True)
        
        # Configuração da Chave Gemini AI
        chave_gemini = st.session_state.get("gemini_api_key", "")
        if not chave_gemini and hasattr(st, "secrets") and "GEMINI_API_KEY" in st.secrets:
            chave_gemini = str(st.secrets["GEMINI_API_KEY"]).strip()
        if not chave_gemini:
            import os
            chave_gemini = os.environ.get("GEMINI_API_KEY", "")

        with st.expander("🔑 Chave de Inteligência Artificial da Manu (Google Gemini)", expanded=not bool(chave_gemini)):
            st.markdown("""
            Para que a Manu leia **o valor exato, data, local e itens** de qualquer foto de cupom fiscal, utilize a visão computacional do Google Gemini.
            * Obtenha sua chave gratuita em: **[Google AI Studio](https://aistudio.google.com/app/apikey)** *(gratuito e sem cartão)*.
            """)
            nova_key = st.text_input("Cole sua chave Gemini API aqui:", value=chave_gemini, type="password", key="input_gemini_key", placeholder="AIzaSy...")
            if nova_key and nova_key.strip() != chave_gemini:
                st.session_state.gemini_api_key = nova_key.strip()
                chave_gemini = nova_key.strip()
                st.success("Chave de IA ativada com sucesso!")

        origem_foto = st.radio(
            "Como deseja enviar o cupom?", 
            ["📁 Escolher da Galeria ou Câmera (Recomendado)", "📷 Câmera ao Vivo no Navegador (Webcam)"], 
            horizontal=True, 
            key="origem_foto_scanner"
        )
        
        imagem_bytes = None
        if origem_foto == "📷 Câmera ao Vivo no Navegador (Webcam)":
            st.caption("ℹ️ *Se a câmera não abrir, verifique se a permissão foi concedida no navegador ou utilize a opção 'Galeria ou Câmera' que usa a câmera nativa do celular.*")
            foto_camera = st.camera_input("Aponte para o cupom ou nota fiscal", key="cam_cupom_ia")
            if foto_camera is not None:
                imagem_bytes = foto_camera.getvalue()
        else:
            st.caption("💡 *No celular, ao tocar no botão abaixo você pode fotografar diretamente com a câmera do smartphone ou selecionar uma foto já tirada.*")
            upload_foto = st.file_uploader("Selecione ou fotografe o recibo/cupom:", type=["jpg", "jpeg", "png"], key="upl_cupom_ia")
            if upload_foto is not None:
                imagem_bytes = upload_foto.getvalue()
                
        if "dados_ia_scanner" not in st.session_state:
            st.session_state.dados_ia_scanner = None
            
        if imagem_bytes is not None:
            col_preview, col_ia = st.columns([1, 1.4])
            with col_preview:
                st.image(imagem_bytes, caption="Cupom Capturado", use_container_width=True)
                if st.button("🔍 ANALISAR COM IA AGORA", use_container_width=True, key="btn_run_ia_scanner"):
                    with st.spinner("Inteligência Artificial analisando texto, valores e categorias..."):
                        resultado_ia = extrair_dados_recibo_ia(imagem_bytes, api_key=chave_gemini)
                        st.session_state.dados_ia_scanner = resultado_ia
                        if resultado_ia.get("sucesso"):
                            st.success("✅ Leitura concluída com sucesso! Confira e edite os campos ao lado.")
                        else:
                            st.warning(resultado_ia.get("mensagem", "Aviso da IA."))
                        
            with col_ia:
                if st.session_state.dados_ia_scanner:
                    d = st.session_state.dados_ia_scanner
                    badge_color = "#10B981" if d.get("sucesso") else "#F59E0B"
                    st.markdown(f'''
                        <div style='background: rgba(16, 185, 129, 0.1); border: 1px solid {badge_color}; border-radius: 8px; padding: 10px 14px; margin-bottom: 15px; font-size: 0.85rem; color: {badge_color};'>
                            ✨ <b>Identificado pela IA:</b> {d.get('origem_ia', 'Leitor Visual')}
                        </div>
                    ''', unsafe_allow_html=True)
                    
                    st.markdown("#### ✍️ Revise e Ajuste as Informações:")
                    with st.form("form_ia_editavel"):
                        ed_desc = st.text_input("Estabelecimento / Descrição", value=d.get("estabelecimento", ""))
                        col_e1, col_e2 = st.columns(2)
                        with col_e1:
                            ed_valor = st.number_input("Valor Total (R$)", value=float(d.get("valor_total", 0.0)), step=1.0, format="%.2f")
                        with col_e2:
                            data_padrao = date.today()
                            try:
                                data_padrao = datetime.strptime(d.get("data", ""), "%Y-%m-%d").date()
                            except Exception:
                                pass
                            ed_data = st.date_input("Data da Emissão", value=data_padrao)
                            
                        sub_ia_sug = inferir_subcategoria_icone(d.get("estabelecimento", "") + " " + d.get("categoria_sugerida", ""), "Despesa")
                        idx_cat = SUBCATEGORIAS_DESPESAS.index(sub_ia_sug) if sub_ia_sug in SUBCATEGORIAS_DESPESAS else 0
                        
                        col_e3, col_e4 = st.columns(2)
                        with col_e3:
                            ed_cat = st.selectbox("Categoria com Ícone (Sugerida pela IA)", SUBCATEGORIAS_DESPESAS, index=idx_cat)
                        with col_e4:
                            ed_conta = st.selectbox("Conta / Meio de Pagamento", ["Cartão de Crédito", "Conta Corrente Principal", "Carteira / Dinheiro Vivo", "Poupança"])
                            
                        ed_itens = st.text_input("Itens Identificados (Opcional)", value=d.get("itens_detectados", ""))
                        
                        salvar_ia = st.form_submit_button("💾 CONFIRMAR E REGISTRAR DESPESA", use_container_width=True)
                        if salvar_ia:
                            if not ed_desc or ed_valor <= 0:
                                st.warning("Informe uma descrição válida e um valor maior que zero.")
                            else:
                                desc_final = f"{ed_desc} ({ed_itens})" if ed_itens else ed_desc
                                cat_503020_ia = MAPA_SUBCATEGORIA_503020.get(ed_cat, "Desejo (30%)")
                                ded_ia = 1 if ed_cat in ["💊 Saúde & Farmácia", "🎓 Educação & Cursos"] else 0
                                adicionar_lancamento(
                                    tipo="Despesa",
                                    descricao=desc_final,
                                    valor=ed_valor,
                                    data_vencimento=ed_data.strftime("%Y-%m-%d"),
                                    categoria=cat_503020_ia,
                                    subcategoria=ed_cat,
                                    conta=ed_conta,
                                    dedutivel=ded_ia,
                                    origem="Scanner IA"
                                )
                                st.session_state.dados_ia_scanner = None
                                st.success(f"✅ Despesa de R$ {ed_valor:,.2f} em '{ed_desc}' ({ed_cat}) registrada com sucesso!")
                                st.rerun()
                else:
                    st.info("👆 Tire uma foto do seu cupom fiscal ou selecione da galeria e clique em **ANALISAR COM IA AGORA** para preencher automaticamente.")

    with tab_manual:
        st.markdown("##### 🏷️ Selecione o Tipo e a Categoria com Ícone")
        col_top1, col_top2 = st.columns(2)
        with col_top1:
            tipo = st.selectbox("Tipo de Lançamento", ["Despesa", "Receita", "Outras Receitas", "Resgate de Investimento"], key="man_tipo_sel")
        with col_top2:
            opcoes_sub_atual = SUBCATEGORIAS_DESPESAS if tipo == "Despesa" else SUBCATEGORIAS_RECEITAS
            subcategoria = st.selectbox("Categoria com Ícone (Detalhada)", opcoes_sub_atual, key="man_subcat_sel")

        cat_503020_sugerida = MAPA_SUBCATEGORIA_503020.get(subcategoria, "Necessidade (50%)" if tipo == "Despesa" else "Renda (Não se aplica)")
        opcoes_503020 = ["Necessidade (50%)", "Desejo (30%)", "Investimento (20%)", "Renda (Não se aplica)"]
        idx_503020 = opcoes_503020.index(cat_503020_sugerida) if cat_503020_sugerida in opcoes_503020 else 0

        sonho_id_form = None
        if tipo == "Despesa" and ("Patrimônio" in subcategoria or cat_503020_sugerida == "Investimento (20%)"):
            df_sonhos_form = database.listar_sonhos(user_id)
            if not df_sonhos_form.empty:
                opcoes_sonhos_f = {"Não vincular a nenhuma Caixinha": None}
                for _, rs in df_sonhos_form.iterrows():
                    pct_f = max(100.0 - (float(rs['valor_atual']) / max(float(rs['valor_alvo']), 0.01) * 100.0), 0.0)
                    opcoes_sonhos_f[f"🎯 {rs['titulo']} (Acumulado: R$ {float(rs['valor_atual']):,.2f} | Falta {pct_f:.1f}%)"] = int(rs['id'])
                escolha_sonho_f = st.selectbox(
                    "🎯 Aplicar este investimento em qual Caixinha / Sonho Planejado?",
                    list(opcoes_sonhos_f.keys()),
                    key="man_sonho_sel"
                )
                sonho_id_form = opcoes_sonhos_f[escolha_sonho_f]

        with st.form(key='form_lancamento'):
            col1, col2 = st.columns(2)
            with col1:
                descricao = st.text_input("Descrição (Ex: Conta de Luz, Supermercado, Uber)")
                valor = st.number_input("Valor (R$)", min_value=0.0, format="%.2f")
                banco = st.text_input("Conta/Banco (Ex: Itaú, Santander)", value="Itaú")
            with col2:
                data_vencimento = st.date_input("Data (Compra/Ocorrência)")
                data_pagamento = st.date_input("Data de Pagamento (Orçamento)", value=data_vencimento)
                categoria = st.selectbox("Regra 50/30/20 (Vinculada automaticamente ao ícone)", opcoes_503020, index=idx_503020)
                status = st.selectbox("Status", ["Pago", "Pendente"], index=0)
                
            st.markdown("---")
            tributavel = False
            dedutivel = False
            if tipo in ["Receita", "Outras Receitas", "Resgate de Investimento", "Informativo"]:
                tributavel = st.checkbox("Rendimento Tributável? (Usado para somar receita na aba de IRPF)")
            elif tipo == "Despesa":
                ded_padrao = subcategoria in ["💊 Saúde & Farmácia", "🎓 Educação & Cursos"]
                dedutivel = st.checkbox("Despesa Dedutível? (Saúde, Educação, INSS pago - Usado na aba de IRPF)", value=ded_padrao)
                
            repetir = st.checkbox("Repetir este lançamento para os próximos meses (Em Lote)")
            meses = 1
            if repetir:
                meses = st.slider("Total de meses (incluindo o primeiro):", min_value=2, max_value=24, value=12)
                
            submit = st.form_submit_button(label="💾 Salvar Lançamento(s)", use_container_width=True)
            
            if submit:
                df_atual = listar_lancamentos()
                duplicado = False
                
                # Verifica se já existe o exato lançamento (mesma desc, valor e vencimento) no mês principal
                data_verificacao = data_vencimento.strftime("%Y-%m-%d")
                if not df_atual.empty:
                    ja_existe = df_atual[
                        (df_atual['descricao'] == descricao) & 
                        (df_atual['valor'] == valor) & 
                        (df_atual['data_vencimento'] == data_verificacao)
                    ]
                    if not ja_existe.empty:
                        duplicado = True
                        
                if duplicado:
                    st.error("Lançamento duplicado! Já existe um item com a mesma descrição, valor e data.")
                else:
                    
                    protocolo = str(uuid.uuid4())[:8].upper()
                    
                    for i in range(meses):
                        # Calcula a data somando os meses
                        nova_data = data_vencimento + relativedelta(months=i)
                        nova_data_pgto = data_pagamento + relativedelta(months=i)
                        data_str = nova_data.strftime("%Y-%m-%d")
                        data_pgto_str = nova_data_pgto.strftime("%Y-%m-%d")
                        
                        # Se for lançamento futuro, já deixa como Pendente automático
                        status_atual = status if i == 0 else "Pendente"
                        
                        desc_nome = descricao if meses == 1 else f"{descricao} ({i+1}/{meses})"
                        
                        val_tributavel = 1 if tributavel else 0
                        val_dedutivel = 1 if dedutivel else 0
                        inserir_lancamento(tipo, desc_nome, valor, data_str, categoria, banco, status_atual, protocolo, data_pgto_str, tributavel=val_tributavel, dedutivel=val_dedutivel, subcategoria=subcategoria)
                        
                    if sonho_id_form is not None and valor > 0:
                        info_ap_f = database.aportar_sonho(user_id, sonho_id_form, valor, registrar_lancamento=False, banco=banco, data_aporte=data_vencimento.strftime("%Y-%m-%d"))
                        if info_ap_f:
                            st.session_state["alerta_aporte_sonho"] = info_ap_f
                            st.info(
                                f"🎯 **Sinalizador de Caixinha ({info_ap_f['titulo']}):** Com este aporte de **R$ {valor:,.2f}**, "
                                f"sua caixinha atingiu **R$ {info_ap_f['novo_valor']:,.2f}** ({info_ap_f['pct_atingido']:.1f}%)! "
                                f"⏳ **Falta apenas {info_ap_f['pct_falta']:.1f}% (R$ {info_ap_f['valor_falta']:,.2f}) para realizar este sonho!**"
                            )

                    if repetir:
                        st.success(f"{meses} lançamentos ({subcategoria}) foram gerados com sucesso para o ano todo!")
                    else:
                        st.success(f"Lançamento salvo com sucesso em {subcategoria}!")

    with tab_csv:
        st.write("#### 📂 Importação em Lote de Despesas (CSV / Extrato Bancário)")
        st.caption("Carregue seu extrato do Itaú ou planilha de despesas (arquivo CSV ou Excel) para lançar todas as contas de uma só vez, com categorização automática da Regra 50/30/20 e detecção de IRPF.")
        
        cfg_col1, cfg_col2, cfg_col3 = st.columns([1.4, 1.2, 1.4])
        with cfg_col1:
            csv_banco = st.text_input("Banco / Conta:", value="Itaú", key="csv_desp_banco")
        with cfg_col2:
            csv_status = st.selectbox("Status dos Lançamentos:", ["Pago", "Pendente"], index=0, key="csv_desp_status")
        with cfg_col3:
            ignorar_dupl = st.checkbox("Ignorar se já existir no extrato", value=True, help="Evita lançamentos duplicados comparando Data, Descrição e Valor com os já salvos no sistema")

        metodo_entrada = st.radio("Forma de envio:", ["📁 Enviar Arquivo (.csv ou .xlsx)", "📋 Colar Texto do CSV"], horizontal=True, key="metodo_envio_desp")
        
        df_csv_raw = None
        
        if metodo_entrada == "📁 Enviar Arquivo (.csv ou .xlsx)":
            arq_upload = st.file_uploader("Selecione o arquivo com as despesas:", type=['csv', 'txt', 'xlsx', 'xls'], key="arq_despesas_csv")
            if arq_upload is not None:
                nome_f = arq_upload.name.lower()
                try:
                    if nome_f.endswith(('.xlsx', '.xls')):
                        df_csv_raw = pd.read_excel(arq_upload)
                    else:
                        conteudo_bytes = arq_upload.getvalue()
                        for enc in ['utf-8-sig', 'latin-1', 'cp1252', 'utf-8', 'iso-8859-1']:
                            for sep in [';', ',', '\t']:
                                try:
                                    t_df = pd.read_csv(io.BytesIO(conteudo_bytes), sep=sep, encoding=enc)
                                    if len(t_df.columns) >= 2 and len(t_df) > 0:
                                        cols_str = " ".join([str(c).lower() for c in t_df.columns])
                                        if any(k in cols_str for k in ['data', 'lan', 'desc', 'valor', 'r$']):
                                            df_csv_raw = t_df
                                            break
                                except Exception:
                                    pass
                            if df_csv_raw is not None:
                                break
                        if df_csv_raw is None:
                            df_csv_raw = pd.read_csv(arq_upload, sep=None, engine='python', encoding='latin-1')
                except Exception as e:
                    st.error(f"Erro ao ler arquivo: {e}")
        else:
            texto_colado = st.text_area("Cole as linhas do CSV aqui (incluindo o cabeçalho se houver):", height=180, placeholder="data;lançamento;ag./origem;valor (R$)\n05/01/2026;PIX TRANSF NISAEL 03/01;;-122,58\n08/01/2026;ENERGIA_EQUATORIAL ESPLANADA V;;-300,27")
            if texto_colado.strip():
                try:
                    for sep in [';', ',', '\t']:
                        try:
                            t_df = pd.read_csv(io.StringIO(texto_colado), sep=sep)
                            if len(t_df.columns) >= 2 and len(t_df) > 0:
                                cols_str = " ".join([str(c).lower() for c in t_df.columns])
                                if any(k in cols_str for k in ['data', 'lan', 'desc', 'valor', 'r$']):
                                    df_csv_raw = t_df
                                    break
                        except Exception:
                            pass
                    if df_csv_raw is None:
                        df_csv_raw = pd.read_csv(io.StringIO(texto_colado), sep=';')
                except Exception as e:
                    st.error(f"Erro ao interpretar o texto colado: {e}")

        if df_csv_raw is not None and not df_csv_raw.empty:
            col_data = None
            col_desc = None
            col_valor = None
            
            for col in df_csv_raw.columns:
                c_clean = str(col).strip().lower()
                if any(k in c_clean for k in ['data', 'dt']):
                    if col_data is None: col_data = col
                elif any(k in c_clean for k in ['lan', 'desc', 'hist', 'origem/destino']):
                    if col_desc is None: col_desc = col
                elif any(k in c_clean for k in ['valor', 'val', 'r$', 'quantia', 'saída', 'debito']):
                    if col_valor is None: col_valor = col
                    
            if not col_data or not col_desc or not col_valor:
                st.warning("Selecione as colunas correspondentes para prosseguir:")
                sc1, sc2, sc3 = st.columns(3)
                col_data = sc1.selectbox("Coluna da Data:", df_csv_raw.columns, index=0 if col_data is None else df_csv_raw.columns.get_loc(col_data))
                col_desc = sc2.selectbox("Coluna da Descrição:", df_csv_raw.columns, index=min(1, len(df_csv_raw.columns)-1) if col_desc is None else df_csv_raw.columns.get_loc(col_desc))
                col_valor = sc3.selectbox("Coluna do Valor:", df_csv_raw.columns, index=len(df_csv_raw.columns)-1 if col_valor is None else df_csv_raw.columns.get_loc(col_valor))
                
            def categorizar_despesa(desc):
                d = str(desc).upper()
                if any(k in d for k in ["INTERNET", "DLS NET", "VERO", "VIVO", "TELEFON", "CELULAR"]):
                    return "Necessidade (50%)", 0
                if any(k in d for k in ["APLICACAO", "APLICAÇÃO", "CDB", "LOTE", "URBANISMO", "G10", "COFRINHO", "TESOURO", "POUPAN"]):
                    return "Investimento (20%)", 0
                if any(k in d for k in ["ESCOLA", "ALANNA", "FACULDADE", "CURSO", "EBPOS", "POS GRADU", "EDITORA BM"]):
                    return "Necessidade (50%)", 1
                if any(k in d for k in ["PSIQUIATRA", "MEDIC", "MÉDIC", "MDIC", "CONSULTA", "EXAME", "HOSPITAL", "CLINICA", "DROGA", "FARMACIA", "FARMÁCIA", "DROGASIL", "RAIA"]):
                    return "Necessidade (50%)", 1
                if any(k in d for k in [
                    "EQUATORIAL", "ENERGIA", "LUZ", "SANEAGO", "AGUA", "ÁGUA", "GUA", "HABITACAO", "HABITAÇÃO", 
                    "CAIXA - HAB", "GCI CAIXA", "IPTU", "IPVA", "DETRAN", "SEFAZ", "DAR", "DAS MEI", 
                    "RECEITA FED", "MULTA", "DNIT", "BANCO GM", "MONTANA", "FINANCIAMENTO", "CRC", "CONSELHO", 
                    "GASOLINA", "ABASTECE", "COMBUSTIVEL", "FAXINA", "DANIELA", "SUPERMERCADO", "ATACAD", 
                    "MERCADO", "COMPRA CARNE", "PADARIA", "PANIF", "CONDOMINIO", "ALUGUEL"
                ]):
                    return "Necessidade (50%)", 0
                if any(k in d for k in [
                    "RENNER", "SHOP", "SHPP", "SHOPEE", "AMAZON", "MERCADO LIVRE", "APPMAX", "KIWIFY", "HOTMART",
                    "RESTAURANTE", "BACIO", "SORVE", "CHURR", "PIZZA", "IFOOD", "BAR", "CAFE", "CAFÉ", "BELEZA",
                    "MODA", "VESTUARIO", "CALCADO", "PARK", "CINEMA", "VIAGEM", "HOTEL", "UBER", "99"
                ]):
                    return "Desejo (30%)", 0
                return "Necessidade (50%)", 0
                
            df_atual_db = listar_lancamentos()
            linhas_despesas = []
            
            for _, r in df_csv_raw.iterrows():
                desc_raw = str(r[col_desc]).strip()
                if not desc_raw or desc_raw.lower() == 'nan':
                    continue
                if any(k in desc_raw.upper() for k in ["SALDO", "TOTAL DISPONIVEL", "TOTAL DISPONÍVEL", "LANÇAMENTOS FUTUROS", "LANCAMENTOS FUTUROS"]):
                    continue
                    
                val_raw = r[col_valor]
                if pd.isna(val_raw):
                    continue
                    
                if isinstance(val_raw, (int, float)):
                    val_num = abs(float(val_raw))
                else:
                    v_str = str(val_raw).strip().replace('R$', '').replace(' ', '')
                    v_str = v_str.replace('.', '').replace(',', '.').replace('-', '')
                    try:
                        val_num = abs(float(v_str))
                    except Exception:
                        continue
                        
                if val_num <= 0:
                    continue
                    
                dt_raw = str(r[col_data]).split(' ')[0].strip()
                try:
                    if '/' in dt_raw:
                        p = dt_raw.split('/')
                        dt_iso = f"{p[2]}-{p[1].zfill(2)}-{p[0].zfill(2)}" if len(p) == 3 else dt_raw
                    elif '-' in dt_raw:
                        p = dt_raw.split('-')
                        dt_iso = dt_raw if len(p[0]) == 4 else f"{p[2]}-{p[1].zfill(2)}-{p[0].zfill(2)}"
                    else:
                        dt_iso = pd.to_datetime(dt_raw).strftime("%Y-%m-%d")
                except Exception:
                    dt_iso = dt_raw
                    
                duplicado = False
                if not df_atual_db.empty:
                    ja_tem = df_atual_db[
                        (df_atual_db['tipo'] == 'Despesa') &
                        (df_atual_db['descricao'] == desc_raw) &
                        (abs(df_atual_db['valor'] - val_num) < 0.01) &
                        (df_atual_db['data_vencimento'] == dt_iso)
                    ]
                    if not ja_tem.empty:
                        duplicado = True
                        
                cat_sug, ded_sug = categorizar_despesa(desc_raw)
                sub_sug = inferir_subcategoria_icone(desc_raw, "Despesa", cat_sug)
                
                linhas_despesas.append({
                    "Data": dt_iso,
                    "Descrição": desc_raw,
                    "Valor (R$)": val_num,
                    "Subcategoria": sub_sug,
                    "Categoria": cat_sug,
                    "Dedutível IRPF": bool(ded_sug),
                    "Banco": csv_banco,
                    "Duplicado": duplicado
                })
                
            if len(linhas_despesas) > 0:
                df_desp_final = pd.DataFrame(linhas_despesas)
                qtd_total = len(df_desp_final)
                qtd_duplicados = int(df_desp_final['Duplicado'].sum())
                
                df_para_salvar = df_desp_final[~df_desp_final['Duplicado']].copy() if ignorar_dupl else df_desp_final.copy()
                df_para_salvar['Data'] = pd.to_datetime(df_para_salvar['Data'], errors='coerce').dt.date.fillna(pd.Timestamp.now().date())
                qtd_novos = len(df_para_salvar)
                total_val = df_para_salvar['Valor (R$)'].sum()
                total_ded = df_para_salvar[df_para_salvar['Dedutível IRPF']]['Valor (R$)'].sum()
                
                st.markdown("---")
                mc1, mc2, mc3, mc4 = st.columns(4)
                mc1.metric("Lançamentos Encontrados", f"{qtd_total} itens")
                mc2.metric("Itens Novos a Importar", f"{qtd_novos} itens", delta=f"-{qtd_duplicados} já existentes" if qtd_duplicados > 0 else "0 duplicados", delta_color="inverse" if qtd_duplicados > 0 else "normal")
                mc3.metric("Total das Despesas Novas", f"R$ {total_val:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
                mc4.metric("Dedutíveis IRPF (Saúde/Educação)", f"R$ {total_ded:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
                
                st.write("##### 📋 Prévia e Ajuste de Categorias:")
                st.caption("Você pode alterar qualquer categoria ou marcar/desmarcar a dedutibilidade do IRPF antes de confirmar:")
                
                df_editavel = st.data_editor(
                    df_para_salvar,
                    column_config={
                        "Data": st.column_config.DateColumn("Data", format="DD/MM/YYYY"),
                        "Descrição": st.column_config.TextColumn("Descrição", width="large"),
                        "Valor (R$)": st.column_config.NumberColumn("Valor (R$)", format="%.2f", help="Valor em Reais (R$)"),
                        "Subcategoria": st.column_config.SelectboxColumn("Categoria (Ícone) 🏷️", options=SUBCATEGORIAS_DESPESAS),
                        "Categoria": st.column_config.SelectboxColumn("Regra 50/30/20", options=["Necessidade (50%)", "Desejo (30%)", "Investimento (20%)", "Renda (Não se aplica)"]),
                        "Dedutível IRPF": st.column_config.CheckboxColumn("Dedutível IRPF?"),
                        "Banco": st.column_config.TextColumn("Banco"),
                        "Duplicado": st.column_config.CheckboxColumn("Já Existe?", disabled=True)
                    },
                    hide_index=True,
                    use_container_width=True,
                    key="editor_despesas_em_lote"
                )
                
                if qtd_novos == 0:
                    st.info("ℹ️ Todos os lançamentos deste arquivo já constam no banco de dados!")
                else:
                    if st.button(f"💾 Confirmar e Salvar {qtd_novos} Despesas no Extrato", type="primary", use_container_width=True):
                        protocolo_desp = f"CSV-DESP-{str(uuid.uuid4())[:6].upper()}"
                        
                        salvos_cont = 0
                        for _, row_item in df_editavel.iterrows():
                            dt_s = str(row_item['Data'])[:10]
                            inserir_lancamento(
                                tipo="Despesa",
                                descricao=str(row_item['Descrição']).strip(),
                                valor=float(row_item['Valor (R$)']),
                                data_vencimento=dt_s,
                                categoria_503020=row_item['Categoria'],
                                banco=str(row_item['Banco']).strip(),
                                status=csv_status,
                                protocolo=protocolo_desp,
                                data_pagamento=dt_s,
                                tributavel=0,
                                dedutivel=1 if row_item['Dedutível IRPF'] else 0,
                                subcategoria=row_item.get('Subcategoria', '📋 Outros')
                            )
                            salvos_cont += 1
                            
                        st.success(f"🎉 **{salvos_cont} despesas salvas com sucesso!** Protocolo do lote: `{protocolo_desp}`")
                        st.balloons()
                        st.rerun()
            else:
                st.warning("Nenhum lançamento de despesa válido encontrado nos dados enviados.")

