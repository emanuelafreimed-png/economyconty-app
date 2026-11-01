import streamlit as st
import pandas as pd
from datetime import datetime, date
import database
from pdf_extractor import extrair_dados_contracheque, extrair_dados_inss, extrair_dados_santander, extrair_dados_extrato_itau
from utils import render_footer_economyconty

def render_leitor_rendas(user_id, nome_usuario="", manu_face_b64=""):
    def listar_lancamentos():
        return database.listar_lancamentos(user_id)
    def inserir_lancamento(tipo, descricao, valor, data_vencimento, categoria="Geral", conta="Conta Principal", status="Realizado", protocolo=None, data_pagamento=None, tributavel=0, dedutivel=0, **kwargs):
        return database.inserir_lancamento(user_id, tipo, descricao, valor, data_vencimento, categoria=categoria, conta=conta, status=status, protocolo=protocolo, data_pagamento=data_pagamento, tributavel=tributavel, dedutivel=dedutivel, **kwargs)

    st.markdown("""
    <div style="margin-bottom: 1.5rem; padding-bottom: 0.8rem; border-bottom: 1px solid rgba(212, 175, 55, 0.2);">
        <h1 style="margin: 0; font-size: 2rem; font-weight: 800; background: linear-gradient(90deg, #F9FAFB, #D4AF37); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
            📄 Robô Leitor de Rendas & Extratos
        </h1>
        <p style="margin: 4px 0 0 0; color: #9CA3AF; font-size: 0.9rem;">Importação inteligente de contra-cheques, informes INSS e extratos bancários em PDF</p>
    </div>
    """, unsafe_allow_html=True)
    
    tipo_doc = st.radio("Selecione o tipo de documento:", ["Contra-Cheque (Caixa Seguradora)", "Extrato de Pagamento (INSS)", "Extrato Bancário (Itaú - Entradas)"])
    arquivo_pdf = st.file_uploader("Arraste seu documento aqui (PDF, Excel ou CSV)", type=["pdf", "xlsx", "xls", "xltx", "csv"], key="uploader_leitor_rendas")
    
    if arquivo_pdf is not None:
        if tipo_doc == "Extrato Bancário (Itaú - Entradas)":
            resultados = []
            ext_nome = arquivo_pdf.name.lower()
            
            if ext_nome.endswith(('.xlsx', '.xls', '.xltx')):
                st.info("📊 Lendo Extrato do Itaú via Excel...")
                try:
                    if hasattr(arquivo_pdf, 'seek'):
                        arquivo_pdf.seek(0)
                    df_raw = pd.read_excel(arquivo_pdf)
                    
                    col_data = [c for c in df_raw.columns if 'data' in str(c).lower()]
                    col_desc = [c for c in df_raw.columns if any(k in str(c).lower() for k in ['lançamento', 'lancamento', 'descri'])]
                    col_valor = [c for c in df_raw.columns if 'valor' in str(c).lower()]
                    
                    if col_data and col_desc and col_valor:
                        c_dt, c_ds, c_vl = col_data[0], col_desc[0], col_valor[0]
                        df_valid = df_raw[df_raw[c_vl].notna() & df_raw[c_ds].notna()].copy()
                        df_valid = df_valid[~df_valid[c_ds].astype(str).str.contains("SALDO", case=False, na=False)]
                        df_valid = df_valid[~df_valid[c_ds].astype(str).str.contains("lançamentos", case=False, na=False)]
                        
                        for _, row in df_valid.iterrows():
                            raw_v = row[c_vl]
                            val_num = pd.to_numeric(str(raw_v).replace('.', '').replace(',', '.'), errors='coerce') if not isinstance(raw_v, (int, float)) else float(raw_v)
                            if pd.isna(val_num) or val_num <= 0:
                                continue
                            dt_raw = str(row[c_dt]).split(' ')[0]
                            if '/' in dt_raw:
                                p = dt_raw.split('/')
                                dt_iso = f"{p[2]}-{p[1]}-{p[0]}" if len(p) == 3 else dt_raw
                            else:
                                dt_iso = dt_raw
                            resultados.append({
                                "Data": dt_iso,
                                "Descricao": str(row[c_ds]).strip(),
                                "Valor": val_num
                            })
                except Exception as e:
                    st.error(f"Erro ao ler arquivo Excel: {e}")
                    
            elif ext_nome.endswith('.csv'):
                st.info("📄 Lendo Extrato do Itaú via CSV...")
                try:
                    if hasattr(arquivo_pdf, 'seek'):
                        arquivo_pdf.seek(0)
                    try:
                        df_csv = pd.read_csv(arquivo_pdf, sep=';', encoding='latin1', skiprows=1, header=None, names=['data', 'lancamento', 'origem', 'valor', 'saldo'])
                    except Exception:
                        arquivo_pdf.seek(0)
                        df_csv = pd.read_csv(arquivo_pdf, sep=',', encoding='utf-8')
                        
                    col_data = [c for c in df_csv.columns if 'data' in str(c).lower()]
                    col_desc = [c for c in df_csv.columns if any(k in str(c).lower() for k in ['lançamento', 'lancamento', 'descri'])]
                    col_valor = [c for c in df_csv.columns if 'valor' in str(c).lower()]
                    
                    if col_data and col_desc and col_valor:
                        c_dt, c_ds, c_vl = col_data[0], col_desc[0], col_valor[0]
                        df_valid = df_csv[df_csv[c_vl].notna() & df_csv[c_ds].notna()].copy()
                        df_valid = df_valid[~df_valid[c_ds].astype(str).str.contains("SALDO", case=False, na=False)]
                        df_valid = df_valid[~df_valid[c_ds].astype(str).str.contains("lançamentos", case=False, na=False)]
                        
                        for _, row in df_valid.iterrows():
                            raw_v = row[c_vl]
                            val_num = pd.to_numeric(str(raw_v).replace('.', '').replace(',', '.'), errors='coerce') if not isinstance(raw_v, (int, float)) else float(raw_v)
                            if pd.isna(val_num) or val_num <= 0:
                                continue
                            dt_raw = str(row[c_dt]).split(' ')[0]
                            if '/' in dt_raw:
                                p = dt_raw.split('/')
                                dt_iso = f"{p[2]}-{p[1]}-{p[0]}" if len(p) == 3 else dt_raw
                            else:
                                dt_iso = dt_raw
                            resultados.append({
                                "Data": dt_iso,
                                "Descricao": str(row[c_ds]).strip(),
                                "Valor": val_num
                            })
                except Exception as e:
                    st.error(f"Erro ao ler arquivo CSV: {e}")
                    
            else:
                st.info("Lendo Extrato do Itaú em PDF...")
                try:
                    import pdfplumber
                    texto_completo = ""
                    if hasattr(arquivo_pdf, 'seek'):
                        arquivo_pdf.seek(0)
                    with pdfplumber.open(arquivo_pdf) as pdf:
                        for pagina in pdf.pages:
                            t = pagina.extract_text()
                            if t:
                                texto_completo += t + "\n"
                                
                    from pdf_extractor import extrair_dados_extrato_itau
                    resultados = extrair_dados_extrato_itau(arquivo_pdf)
                    
                    if len(resultados) == 0:
                        if len(texto_completo.strip()) == 0:
                            st.warning("⚠️ **Arquivo PDF sem texto pesquisável:** Este documento foi impresso ou digitalizado como imagem (sem texto digital).")
                            st.info("💡 **Dica EconomyContY:** Como o extrato oficial do Itaú é gerado originalmente em **Excel (.xlsx ou .xltx)** ou **CSV**, faça o upload do arquivo Excel ou CSV diretamente aqui! O nosso leitor agora processa planilhas nativamente com 100% de precisão!")
                        else:
                            st.warning("Não conseguimos achar créditos no padrão esperado no texto do PDF. Veja o texto bruto:")
                            st.text_area("Texto Bruto do Itaú", texto_completo, height=300)
                except Exception as e:
                    st.error(f"Erro ao ler o Extrato em PDF: {e}")
                    
            if len(resultados) > 0:
                for r in resultados:
                    desc_u = str(r['Descricao']).upper()
                    if any(k in desc_u for k in ["COR RESGATE TD.", "DI RESGATE CDB", "RESGATE CDB DI"]):
                        r['Tipo'] = "Resgate de Investimento"
                        r['Categoria'] = "Investimento (20%)"
                    elif any(k in desc_u for k in ["PGTO INSS 01525714241", "TED 104.0630.EMANUELA K"]):
                        r['Tipo'] = "Receita"
                        r['Categoria'] = "Renda (Não se aplica)"
                    else:
                        r['Tipo'] = "Outras Receitas"
                        r['Categoria'] = "Renda (Não se aplica)"
                
                st.success(f"Encontramos {len(resultados)} entradas no extrato!")
                df_prev = pd.DataFrame(resultados)
                st.dataframe(df_prev, width="stretch", hide_index=True)
                
                st.markdown("---")
                if st.button("Salvar Entradas do Extrato"):
                    import uuid
                    protocolo_ext = str(uuid.uuid4())[:8].upper()
                    for dados in resultados:
                        inserir_lancamento(
                            tipo=dados.get('Tipo', 'Receita'),
                            descricao=dados['Descricao'],
                            valor=dados['Valor'],
                            data_vencimento=dados['Data'],
                            categoria_503020=dados.get('Categoria', 'Renda (Não se aplica)'),
                            banco="Itaú",
                            status="Pago",
                            protocolo=protocolo_ext,
                            data_pagamento=dados['Data']
                        )
                    st.success(f"{len(resultados)} lançamento(s) adicionado(s) com categorização automática ao banco de dados com sucesso!")
            elif ext_nome.endswith(('.xlsx', '.xls', '.xltx', '.csv')):
                st.warning("Nenhum lançamento de crédito válido encontrado no arquivo enviado.")
                
        elif tipo_doc == "Contra-Cheque (Caixa Seguradora)":
            st.info("Extraindo dados do(s) Contra-Cheque(s)...")
            try:
                resultados = extrair_dados_contracheque(arquivo_pdf)
                st.success(f"Leitura concluída! Encontramos {len(resultados)} contra-cheque(s) no documento.")
                
                if len(resultados) > 0:
                    for dados in resultados:
                        st.write(f"✔️ **{dados['Mes_Referencia']}**: Salário Líquido R$ {dados['Salario_Liquido']:.2f}")
                        
                    st.markdown("---")
                    if st.button("Salvar Dados (Apenas para Validação de IRPF)"):
                        for dados in resultados:
                            mes, ano = dados['Mes_Referencia'].split('/')
                            # Último dia útil do mês
                            data_venc = pd.bdate_range(start=f'{ano}-{mes}-01', periods=1, freq='BME')[0].strftime("%Y-%m-%d")
                            
                            # Salva apenas os registros como "Informativo" para não duplicar com o extrato bancário
                            
                            # 1. Salário Bruto (Informativo)
                            inserir_lancamento(
                                tipo="Informativo",
                                descricao=f"Salário Bruto Caixa Seguradora ({dados['Mes_Referencia']})",
                                valor=dados['Salario_Bruto'],
                                data_vencimento=data_venc,
                                categoria_503020="Renda (Não se aplica)",
                                banco="Caixa Seguradora",
                                status="Pago"
                            )
                            
                            # 2. INSS (Informativo)
                            if dados['INSS'] > 0:
                                inserir_lancamento(
                                    tipo="Informativo",
                                    descricao=f"INSS Retido ({dados['Mes_Referencia']})",
                                    valor=dados['INSS'],
                                    data_vencimento=data_venc,
                                    categoria_503020="Necessidade (50%)",
                                    banco="Caixa Seguradora",
                                    status="Pago"
                                )
                                
                            # 3. IRRF (Informativo)
                            if dados['IRRF'] > 0:
                                inserir_lancamento(
                                    tipo="Informativo",
                                    descricao=f"IRRF Retido ({dados['Mes_Referencia']})",
                                    valor=dados['IRRF'],
                                    data_vencimento=data_venc,
                                    categoria_503020="Necessidade (50%)",
                                    banco="Caixa Seguradora",
                                    status="Pago"
                                )
                                
                        st.success(f"{len(resultados)} meses salvos como 'Informativo' para alimentar o painel de IRPF sem duplicar seu saldo!")
                else:
                    st.warning("Nenhum contra-cheque reconhecido neste PDF.")
                    
            except Exception as e:
                st.error(f"Erro ao ler o PDF: {e}")
                
        elif tipo_doc == "Extrato de Pagamento (INSS)":
            st.info("Extraindo histórico do INSS...")
            try:
                dados_inss = extrair_dados_inss(arquivo_pdf)
                st.success(f"Encontrou {len(dados_inss)} pagamentos do INSS no documento!")
                
                if len(dados_inss) == 0:
                    try:
                        import pdfplumber
                        arquivo_pdf.seek(0)
                        texto = ""
                        with pdfplumber.open(arquivo_pdf) as pdf:
                            for pagina in pdf.pages:
                                extraido = pagina.extract_text()
                                if extraido:
                                    texto += extraido + "\n"
                        if len(texto.strip()) == 0:
                            st.warning("⚠️ **Arquivo PDF sem texto digital:** Este PDF do INSS não possui camada de texto legível (foi digitalizado ou impresso como imagem).")
                            st.info("💡 **Dica EconomyContY:** O portal Meu INSS disponibiliza o arquivo oficial **'Histórico de Créditos'** (`historico-creditos.pdf`). Ao fazer o download direto do portal Meu INSS sem imprimir, ele contém o texto digital e nosso leitor extrai todas as competências automaticamente!")
                        else:
                            st.warning("Não conseguimos encontrar o padrão de competências e valores no texto do PDF. Veja o texto bruto:")
                            st.text_area("Texto Bruto do INSS", texto, height=300)
                            with open("inss_raw.txt", "w", encoding="utf-8") as f_dump:
                                f_dump.write(texto)
                    except Exception as e:
                        st.error(f"Erro ao extrair texto bruto: {e}")
                else:
                    df_inss_prev = pd.DataFrame(dados_inss).rename(columns={
                        "Mes_Referencia": "Mês de Referência",
                        "Salario_Liquido": "Valor Líquido (R$)",
                        "Descricao": "Descrição"
                    })
                    st.dataframe(df_inss_prev, width="stretch", hide_index=True)
                    
                    st.markdown("---")
                    if st.button("Salvar Dados (Apenas para Histórico Informativo)"):
                        for dado in dados_inss:
                            mes, ano = dado['Mes_Referencia'].split('/')
                            # 4º dia útil do mês
                            data_venc = pd.bdate_range(start=f'{ano}-{mes}-01', periods=4, freq='B')[3].strftime("%Y-%m-%d")
                            
                            inserir_lancamento(
                                tipo="Informativo", 
                                descricao=dado['Descricao'], 
                                valor=dado['Salario_Liquido'], 
                                data_vencimento=data_venc, 
                                categoria_503020="Renda (Não se aplica)", 
                                banco="INSS", 
                                status="Pago"
                            )
                        st.success("Histórico do INSS salvo como 'Informativo' com sucesso (sem duplicar seu extrato)!")
            except Exception as e:
                st.error(f"Erro ao ler o PDF do INSS: {e}")

