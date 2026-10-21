import pdfplumber
import re

def extrair_dados_contracheque(arquivo_pdf):
    if hasattr(arquivo_pdf, 'seek'):
        arquivo_pdf.seek(0)
    resultados = []
    
    with pdfplumber.open(arquivo_pdf) as pdf:
        for pagina in pdf.pages:
            texto = pagina.extract_text()
            if not texto:
                continue
                
            # Busca Referência nesta página (Ex: 09/2026)
            match_ref = re.search(r'(\d{2}/\d{4})\s*$', texto, re.MULTILINE)
            if not match_ref:
                continue
                
            dados = {
                "Mes_Referencia": match_ref.group(1),
                "Salario_Bruto": 0.0,
                "Total_Descontos": 0.0,
                "Salario_Liquido": 0.0,
                "INSS": 0.0,
                "IRRF": 0.0
            }
            
            match_proventos = re.search(r'Total de proventos:\s*([\d.]*,\d{2})', texto)
            if match_proventos:
                dados["Salario_Bruto"] = float(match_proventos.group(1).replace('.', '').replace(',', '.'))
                
            match_liquido = re.search(r'Total líquido:\s*([\d.]*,\d{2})', texto)
            if match_liquido:
                dados["Salario_Liquido"] = float(match_liquido.group(1).replace('.', '').replace(',', '.'))
                
            match_inss = re.search(r'INSS MES\s*([\d.]*,\d{2})', texto)
            if match_inss:
                dados["INSS"] = float(match_inss.group(1).replace('.', '').replace(',', '.'))
                
            match_irrf = re.search(r'IRRF MES\s*([\d.]*,\d{2})', texto)
            if match_irrf:
                dados["IRRF"] = float(match_irrf.group(1).replace('.', '').replace(',', '.'))
                
            match_desc = re.search(r'Total de descontos:\s*([\d.]*,\d{2})', texto)
            if match_desc:
                dados["Total_Descontos"] = float(match_desc.group(1).replace('.', '').replace(',', '.'))
                
            dados["Adiantamento"] = 0.0
            
            # Tratamento especial: Pegar o Adiantamento Quinzenal (código 07220)
            linha_adiantamento = re.search(r'07220.*', texto)
            if linha_adiantamento:
                valores = re.findall(r'[\d.]*,\d{2}', linha_adiantamento.group(0))
                if valores:
                    dados["Adiantamento"] = float(valores[-1].replace('.', '').replace(',', '.'))
                
            resultados.append(dados)
            
    # Filtra duplicatas e permite apenas o ano de 2026
    unicos = {}
    for r in resultados:
        if r["Mes_Referencia"].endswith("/2026"):
            if r["Mes_Referencia"] not in unicos:
                unicos[r["Mes_Referencia"]] = r
            
    return list(unicos.values())

def extrair_dados_inss(arquivo_pdf):
    texto = ""
    with pdfplumber.open(arquivo_pdf) as pdf:
        for pagina in pdf.pages:
            extraido = pagina.extract_text()
            if extraido:
                texto += extraido + "\n"
                
    # DUMP TO TXT FOR DEBUG
    with open('inss_raw.txt', 'w', encoding='utf-8') as f:
        f.write(texto)

    # O INSS possui um formato tabular, vamos buscar as linhas que tem a competência e o Valor Líquido
    # Exemplo: "01/2026 01/01/2026 R$ 2.961,20"
    padrao = r'(\d{2}/\d{4})\s+\d{2}/\d{2}/\d{4}\s+R\$\s*([\d.]*,\d{2})'
    encontrados = re.findall(padrao, texto)
    
    resultados = []
    vistos = {} # Para evitar duplicatas caso a mesma competência apareça duas vezes na página
    
    for comp, valor in encontrados:
        if comp not in vistos:
            vistos[comp] = float(valor.replace('.', '').replace(',', '.'))
            
    for comp, valor in vistos.items():
        if comp.endswith("/2026"):
            resultados.append({
                "Mes_Referencia": comp,
                "Salario_Liquido": valor,
                "Descricao": f"Benefício INSS ({comp})"
            })
        
    return resultados

def extrair_dados_extrato_itau(arquivo_pdf):
    if hasattr(arquivo_pdf, 'seek'):
        arquivo_pdf.seek(0)
    texto = ""
    import pdfplumber
    with pdfplumber.open(arquivo_pdf) as pdf:
        for pagina in pdf.pages:
            extraido = pagina.extract_text()
            if extraido:
                texto += extraido + "\n"
                
    # Procura por linhas do tipo: DD/MM/YYYY [DESCRICAO] VALOR
    # Suporta TED, PIX, DOC, SALÁRIO, PGTO INSS, RESGATES, RENDIMENTOS, etc.
    padrao = r'(\d{2}/\d{2}/\d{4})\s+([A-Za-z0-9\.\-\/\s\*\#\_\+]+?)\s+([\d\.]*,\d{2})(?:\s|$)'
    resultados = []
    for linha in texto.split('\n'):
        linha = linha.strip()
        m = re.search(padrao, linha)
        if m:
            data_str, desc, valor_str = m.groups()
            desc_clean = desc.strip()
            # Ignora saldos ou linhas de cabeçalho
            if any(termo in desc_clean.upper() for termo in ["SALDO", "DISPONÍVEL", "DISPONIVEL", "TOTAL", "LANÇAMENTO", "LANCAMENTO"]):
                continue
            # Ignora saídas/débitos se houver sinal negativo ou indicador (D)
            if '-' in valor_str or '(D)' in linha.upper() or 'DÉBITO' in linha.upper():
                continue
            try:
                dia, mes, ano = data_str.split('/')
                data_iso = f"{ano}-{mes}-{dia}"
                valor = float(valor_str.replace('.', '').replace(',', '.'))
                if valor > 0:
                    resultados.append({
                        "Data": data_iso,
                        "Descricao": desc_clean,
                        "Valor": valor
                    })
            except Exception:
                pass
                
    return resultados

def extrair_dados_santander(arquivo_pdf):
    if hasattr(arquivo_pdf, 'seek'):
        arquivo_pdf.seek(0)
    resultados = []
    texto_completo = ""
    
    with pdfplumber.open(arquivo_pdf) as pdf:
        for pagina in pdf.pages:
            texto = pagina.extract_text()
            if not texto:
                continue
                
            texto_completo += texto + "\n"
            
            for linha in texto.split('\n'):
                # O PDF do Santander mistura a coluna de resumo (da direita) e cabeçalhos (da esquerda) na mesma linha das compras.
                # Removemos a parte indesejada antes do regex
                for termo_dir in [" (-) Total", " (+) Total", " (=) Saldo", " Saldo Anterior", " Resumo da Fatura", " Descrição R$ US$", " Descrio R$ US$", " crédito e tarifas", " crdito e tarifas"]:
                    if termo_dir in linha:
                        linha = linha.split(termo_dir)[0]
                
                for termo_esq in ["Parcelamentos", "Compra Data Descrição Parcela R$ US$", "Compra Data Descrio Parcela R$ US$"]:
                    linha = linha.replace(termo_esq, '')
                    
                linha = linha.strip()
                
                # Agora usamos finditer para extrair todas as compras presentes na mesma linha
                for m in re.finditer(r'(\d{2}/\d{2})\s+((?:(?!\d{2}/\d{2}).)+?)\s+(?:(\d{2}/\d{2})\s+)?([-]?[\d.]*,\d{2})(?:\s|$)', linha):
                    data, desc, parcela, valor_str = m.groups()
                    desc = desc.strip()
                    
                    # Filtramos ignorando pagamentos de fatura ou saldos específicos deste match
                    desc_upper = desc.upper()
                    if "PAGAMENTO DE FATURA" in desc_upper or "SALDO ANTERIOR" in desc_upper or "VALOR TOTAL" in desc_upper:
                        continue
                        
                    # Conversão de valor
                    try:
                        valor_num = float(valor_str.replace('.', '').replace(',', '.'))
                    except ValueError:
                        continue
                        
                    # Ignoramos pagamentos
                    if valor_num == 0:
                        continue
                        
                    parcela_str = parcela if parcela else "-"
                    
                    resultados.append({
                        "Data": data,
                        "Descrição": desc,
                        "Parcela": parcela_str,
                        "Valor": valor_num,
                        "Tipo": "Despesa"
                    })
                
    # Verifica se há diferença entre o total extraído e o Total a Pagar real da fatura
    s_match = re.search(r'\(\=\) Saldo Desta Fatura\s+([\d,.]+)', texto_completo)
    v_match = re.search(r'Pagável preferencialmente no banco Santander\s+(\d{2}/\d{2}/\d{4})', texto_completo)
    
    if s_match and v_match:
        saldo_real = float(s_match.group(1).replace('.', '').replace(',', '.'))
        venc_str = v_match.group(1)[:5]  # ex: 06/10
        total_extraido = sum(l['Valor'] for l in resultados)
        
        diferenca = saldo_real - total_extraido
        
        # Se a diferença for maior que 1 centavo, adiciona o lançamento
        if round(diferenca, 2) > 0.01:
            resultados.append({
                "Data": venc_str,
                "Descrição": "Ajuste de Fatura (Encargos, Juros ou IOF)",
                "Parcela": "-",
                "Valor": round(diferenca, 2),
                "Tipo": "Despesa"
            })

    return resultados
