import base64
import json
import re
from datetime import datetime
import requests
import io
from PIL import Image

def redimensionar_e_otimizar_imagem(image_bytes, max_dim=1024):
    """Otimiza a imagem para envio rápido à IA mantendo a legibilidade do texto."""
    try:
        img = Image.open(io.BytesIO(image_bytes))
        # Converter para RGB se for RGBA
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
            
        w, h = img.size
        if max(w, h) > max_dim:
            if w > h:
                new_w = max_dim
                new_h = int(h * (max_dim / w))
            else:
                new_h = max_dim
                new_w = int(w * (max_dim / h))
            img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
            
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG", quality=85)
        return buffer.getvalue()
    except Exception:
        return image_bytes

def extrair_dados_recibo_ia(image_bytes, api_key=None):
    """
    Analisa a imagem do recibo ou cupom fiscal usando Inteligência Artificial de Visão.
    Retorna um dicionário estruturado com:
    - estabelecimento
    - valor_total
    - data
    - categoria_sugerida
    - itens_detectados
    - confianca
    """
    otimizada = redimensionar_e_otimizar_imagem(image_bytes)
    b64_image = base64.b64encode(otimizada).decode('utf-8')
    
    # Se houver uma chave de API do Google Gemini fornecida, usa a visão multimodal Gemini 1.5 Flash
    if api_key and len(api_key.strip()) > 10:
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key.strip()}"
            headers = {"Content-Type": "application/json"}
            
            prompt = """
            Você é um assistente contábil especializado em ler cupons fiscais e recibos brasileiros (NFC-e, SAT, recibos manuais).
            Analise a imagem deste cupom fiscal ou recibo e extraia EXATAMENTE em formato JSON puro:
            {
                "estabelecimento": "Nome do comércio ou prestador de serviço",
                "valor_total": 0.00,
                "data": "AAAA-MM-DD",
                "categoria_sugerida": "Alimentação | Transporte | Moradia | Saúde | Educação | Lazer | Serviços | Outros",
                "itens_detectados": "Resumo dos principais itens ou serviços comprados"
            }
            Atenção: retorne APENAS o JSON válido, sem crases de markdown e sem explicações adicionais.
            """
            
            payload = {
                "contents": [{
                    "parts": [
                        {"text": prompt},
                        {
                            "inline_data": {
                                "mime_type": "image/jpeg",
                                "data": b64_image
                            }
                        }
                    ]
                }],
                "generationConfig": {
                    "temperature": 0.1,
                    "response_mime_type": "application/json"
                }
            }
            
            response = requests.post(url, headers=headers, json=payload, timeout=25)
            if response.status_code == 200:
                res_data = response.json()
                texto_json = res_data['candidates'][0]['content']['parts'][0]['text']
                # Limpar possíveis crases e formatação markdown
                texto_json = re.sub(r'^```json\s*', '', texto_json)
                texto_json = re.sub(r'\s*```$', '', texto_json)
                texto_json = texto_json.strip()
                dados = json.loads(texto_json)
                return {
                    "sucesso": True,
                    "origem_ia": "Google Gemini Vision AI (Visão Multimodal)",
                    "estabelecimento": str(dados.get("estabelecimento", "Estabelecimento Comercial")),
                    "valor_total": float(dados.get("valor_total", 0.0)),
                    "data": str(dados.get("data", datetime.now().strftime("%Y-%m-%d"))),
                    "categoria_sugerida": str(dados.get("categoria_sugerida", "Outros")),
                    "itens_detectados": str(dados.get("itens_detectados", "")),
                }
            else:
                err_msg = "Chave de API inválida ou limite atingido."
                try:
                    res_err = response.json()
                    err_msg = res_err.get('error', {}).get('message', err_msg)
                except Exception:
                    pass
                return {
                    "sucesso": False,
                    "mensagem": f"Falha na API Google Gemini ({response.status_code}): {err_msg}",
                    "estabelecimento": "",
                    "valor_total": 0.0,
                    "data": datetime.now().strftime("%Y-%m-%d"),
                    "categoria_sugerida": "Outros",
                    "itens_detectados": "",
                }
        except Exception as e:
            return {
                "sucesso": False,
                "mensagem": f"Erro de conexão com o serviço de IA: {str(e)}",
                "estabelecimento": "",
                "valor_total": 0.0,
                "data": datetime.now().strftime("%Y-%m-%d"),
                "categoria_sugerida": "Outros",
                "itens_detectados": "",
            }

    # Sem chave de IA fornecida: orienta o usuário de forma clara
    agora_str = datetime.now().strftime("%Y-%m-%d")
    return {
        "sucesso": False,
        "mensagem": "Nenhuma chave do Google Gemini foi informada. Insira sua chave gratuita de IA no campo acima para ativar o reconhecimento visual automático.",
        "origem_ia": "Entrada Manual (Aguardando Chave de IA)",
        "estabelecimento": "",
        "valor_total": 0.0,
        "data": agora_str,
        "categoria_sugerida": "Outros",
        "itens_detectados": "",
    }
