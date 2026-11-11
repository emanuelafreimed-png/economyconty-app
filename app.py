import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date
import os

from auth import init_auth_db, verificar_credenciais, cadastrar_usuario, alterar_senha, TERMO_ACEITE_LGPD_TEXTO
from database import (
    init_db, adicionar_lancamento, excluir_lancamento, 
    carregar_lancamentos, obter_resumo_kpis, processar_e_importar_csv,
    SUBCATEGORIAS_DESPESAS, SUBCATEGORIAS_RECEITAS, TODAS_SUBCATEGORIAS,
    MAPA_SUBCATEGORIA_503020, inferir_subcategoria_icone,
    ICONES_SONHOS, listar_sonhos, criar_sonho, aportar_sonho, excluir_sonho
)
from ai_scanner import extrair_dados_recibo_ia


# Inicializar Bancos
init_auth_db()
init_db()

st.set_page_config(
    page_title="EconomyContY • Inteligência Financeira",
    page_icon="👑",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilização Executiva Premium
st.html("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@600;700;800&family=Playfair+Display:ital,wght@0,600;0,700;0,800;1,600&family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap');

/* --- VARIÁVEIS OFICIAIS DO GUIA DE IDENTIDADE CROMÁTICA V1.0 --- */
:root {
    --verde-petroleo: #193035;       /* Fundo estrutural e institucional */
    --azul-petroleo: #0E3646;        /* Quadros técnicos e informativos */
    --azul-marinho: #16253D;         /* Rodapés e fundos especiais */
    --vinho-profundo: #4A1728;       /* Títulos expressivos e alertas estratégicos */
    --ameixa-elegante: #7D5768;      /* Apoio, subtítulos e ícones */
    --dourado-champagne: #C2A35C;    /* Ênfase: filetes, selos, números (5%) */
    --dourado-intenso: #B88A2D;      /* Destaques, hover e grafismos */
    --marfim: #F9F8F4;               /* Textos claros, respiro e composição */
}

html, body, [class*="css"] {
    font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif !important;
}

h1, h2, h3, .brand-title {
    font-family: 'Georgia', 'Playfair Display', serif !important;
    letter-spacing: 0.02em;
    text-transform: none !important;
}

h4, h5, h6, .stMarkdown h4, .stMarkdown h5 {
    color: #FFDE7A !important;
    font-weight: 700 !important;
    text-shadow: 0 1px 3px rgba(0,0,0,0.8);
}

/* Fundo Executivo - Verde-Petróleo Profundo & Azul-Marinho */
.stApp {
    background: radial-gradient(circle at 85% 15%, #0E3646 0%, #193035 50%, #0F1D21 100%) !important;
    color: #F9F8F4 !important;
}

/* Sidebar Padronizada com Verde-Petróleo e Filetes Dourados */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #132428 0%, #0E1A1D 100%) !important;
    border-right: 1px solid rgba(194, 163, 92, 0.25) !important;
}

/* Card de KPI */
.kpi-card {
    background: linear-gradient(135deg, rgba(25, 48, 53, 0.85) 0%, rgba(14, 54, 70, 0.9) 100%);
    border: 1px solid rgba(194, 163, 92, 0.3);
    border-radius: 12px;
    padding: 18px 20px;
    box-shadow: 0 10px 28px rgba(0, 0, 0, 0.4);
    backdrop-filter: blur(12px);
    transition: transform 0.2s ease, border-color 0.2s ease, box-shadow 0.2s ease;
}
.kpi-card:hover {
    transform: translateY(-2px);
    border-color: #C2A35C;
    box-shadow: 0 12px 32px rgba(194, 163, 92, 0.15);
}
.kpi-label {
    font-size: 0.82rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: #FFDE7A !important; /* Dourado Luminoso para legibilidade máxima */
    margin-bottom: 6px;
    text-shadow: 0 1px 3px rgba(0,0,0,0.8);
}
.kpi-val {
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    font-size: 1.65rem;
    font-weight: 800;
    color: #FFFFFF !important; /* Branco Puro para clareza máxima */
}

/* Cores de Destaque Oficiais */
.gold-text { color: #FFDE7A !important; }
.gold-intense { color: #E6CA65 !important; }
.green-text { color: #10B981 !important; }
.red-text { color: #EF4444 !important; }
.wine-text { color: #FFDE7A !important; }
.plum-text { color: #E2EEF0 !important; }

/* Botões Customizados - Dourado Champagne & Ouro Vibrante */
.stButton > button {
    background: linear-gradient(135deg, #FFDE7A 0%, #D4AF37 50%, #B88928 100%) !important;
    color: #041418 !important; /* Texto Escuro Executivo para Contraste Máximo */
    font-weight: 800 !important;
    border: none !important;
    border-radius: 8px !important;
    padding: 10px 24px !important;
    transition: all 0.3s ease !important;
    letter-spacing: 0.03em !important;
    box-shadow: 0 4px 14px rgba(212, 175, 55, 0.35) !important;
}
.stButton > button:hover {
    box-shadow: 0 0 20px rgba(255, 222, 122, 0.6) !important;
    transform: scale(1.02) !important;
}

/* Abas de Navegação Globais */
.stTabs [data-baseweb="tab-list"] {
    gap: 8px;
    border-bottom: 1.5px solid rgba(212, 175, 55, 0.35) !important;
    background: rgba(4, 20, 24, 0.6) !important;
    border-radius: 10px 10px 0 0 !important;
    padding: 4px 6px !important;
}
.stTabs [data-baseweb="tab"] {
    padding: 10px 18px;
    border-radius: 8px 8px 0 0;
    transition: all 0.2s ease !important;
}
.stTabs [data-baseweb="tab"] p, 
.stTabs [data-baseweb="tab"] span {
    color: #B5D5DC !important; /* Prata Ciano Nítido */
    font-weight: 600 !important;
    font-size: 0.92rem !important;
}
.stTabs [data-baseweb="tab"]:hover p {
    color: #FFDE7A !important;
}
.stTabs [aria-selected="true"] {
    background: rgba(212, 175, 55, 0.2) !important;
    border-bottom: 2.5px solid #FFDE7A !important;
}
.stTabs [aria-selected="true"] p, 
.stTabs [aria-selected="true"] span {
    color: #FFDE7A !important;
    font-weight: 800 !important;
}

/* Navegação da Barra Lateral (Sidebar) com Alto Contraste */
section[data-testid="stSidebar"] [data-testid="stRadio"] label,
section[data-testid="stSidebar"] [data-testid="stRadio"] label p,
section[data-testid="stSidebar"] [data-testid="stRadio"] label span {
    color: #E2EEF0 !important;
    font-weight: 600 !important;
    font-size: 0.95rem !important;
    opacity: 1 !important;
}
section[data-testid="stSidebar"] [data-testid="stRadio"] label:hover p {
    color: #FFDE7A !important;
}
section[data-testid="stSidebar"] [data-testid="stRadio"] div[aria-checked="true"] + div p,
section[data-testid="stSidebar"] [data-testid="stRadio"] label[data-checked="true"] p {
    color: #FFDE7A !important;
    font-weight: 800 !important;
}

/* Rótulos de Formulários e Widgets Globais (Alto Contraste Ouro) */
.stSelectbox label, .stSelectbox label p,
.stMultiSelect label, .stMultiSelect label p,
.stDateInput label, .stDateInput label p,
.stNumberInput label, .stNumberInput label p,
.stTextInput label, .stTextInput label p,
.stTextArea label, .stTextArea label p,
[data-testid="stWidgetLabel"], [data-testid="stWidgetLabel"] p, [data-testid="stWidgetLabel"] span {
    color: #FFDE7A !important;
    font-weight: 700 !important;
    font-size: 0.92rem !important;
    text-shadow: 0 1px 3px rgba(0,0,0,0.8) !important;
    opacity: 1 !important;
}

/* Rádio Buttons Internos das Páginas */
[data-testid="stRadio"] label p, 
[data-testid="stRadio"] label span {
    color: #F0F6F8 !important;
    font-weight: 600 !important;
    font-size: 0.92rem !important;
}

/* Subtítulos e Textos Gerais Nítidos */
.stMarkdown p, .stMarkdown span {
    color: #E2EEF0;
}

/* Badges e Selos */
.brand-badge {
    background: rgba(212, 175, 55, 0.18);
    border: 1px solid rgba(212, 175, 55, 0.45);
    border-radius: 20px;
    padding: 4px 14px;
    font-size: 0.76rem;
    color: #FFDE7A;
    font-weight: 700;
    display: inline-block;
}
</style>
""")

# Gestão de Sessão do Usuário
if "usuario_logado" not in st.session_state:
    st.session_state.usuario_logado = False
    st.session_state.user_id = None
    st.session_state.nome_usuario = ""
    st.session_state.plano_usuario = "Gratuito"

# ==============================================================================
# TELA DE LOGIN & CADASTRO (MULTI-TENANT / COMERCIAL)
# ==============================================================================
if not st.session_state.usuario_logado:
    st.html("""
    <style>
    /* Fundo da Página em Esmeralda Profundo Executivo */
    .stApp {
        background: radial-gradient(circle at 75% 25%, #0B2B33 0%, #06191E 55%, #030F12 100%) !important;
    }
    .block-container {
        padding-top: max(1.5rem, calc((100vh - 660px) / 2)) !important;
        padding-bottom: 1.5rem !important;
        max-width: 1140px !important;
        margin: 0 auto !important;
    }
    header[data-testid="stHeader"] {
        background: transparent !important;
        height: 2.2rem !important;
    }

    /* Rótulos dos Campos com Máxima Visibilidade (Ouro Imperial) */
    .stTextInput label, 
    .stTextInput label *, 
    [data-testid="stWidgetLabel"], 
    [data-testid="stWidgetLabel"] * {
        color: #FFDE7A !important;
        font-weight: 800 !important;
        font-size: 0.95rem !important;
        letter-spacing: 0.5px !important;
        text-shadow: 0 1px 4px rgba(0,0,0,0.9) !important;
        opacity: 1 !important;
    }

    /* Abas de Navegação (Opções: Entrar na Conta / Criar Nova Conta) */
    [data-baseweb="tab-list"] {
        background: rgba(3, 16, 20, 0.9) !important;
        border: 1.5px solid rgba(212, 175, 55, 0.45) !important;
        border-radius: 12px !important;
        padding: 6px !important;
        margin-bottom: 20px !important;
        gap: 8px !important;
    }
    [data-baseweb="tab"] {
        background: rgba(255, 255, 255, 0.08) !important;
        border: 1px solid rgba(212, 175, 55, 0.25) !important;
        border-radius: 8px !important;
        padding: 10px 18px !important;
        transition: all 0.25s ease !important;
    }
    [data-baseweb="tab"] * {
        color: #E2EEF0 !important;
        font-weight: 700 !important;
        font-size: 0.95rem !important;
        opacity: 1 !important;
    }
    [data-baseweb="tab"]:hover {
        background: rgba(212, 175, 55, 0.2) !important;
    }
    [data-baseweb="tab"]:hover * {
        color: #FFF2C2 !important;
    }
    [data-baseweb="tab"][aria-selected="true"] {
        background: linear-gradient(135deg, rgba(212, 175, 55, 0.35) 0%, rgba(11, 48, 56, 0.9) 100%) !important;
        border: 1.5px solid #FFDE7A !important;
        border-bottom: 3px solid #FFDE7A !important;
        box-shadow: 0 4px 16px rgba(212, 175, 55, 0.35) !important;
    }
    [data-baseweb="tab"][aria-selected="true"] * {
        color: #FFFFFF !important;
        font-weight: 800 !important;
        text-shadow: 0 1px 4px rgba(0,0,0,0.8) !important;
    }

    /* Campos de Entrada (Harmonia Esmeralda e Borda Dourada Nítida) */
    [data-baseweb="input"], .stTextInput > div > div {
        background: rgba(5, 24, 30, 0.9) !important;
        border: 1.5px solid rgba(212, 175, 55, 0.45) !important;
        border-radius: 10px !important;
        transition: all 0.25s ease !important;
    }
    [data-baseweb="input"]:focus-within, .stTextInput > div > div:focus-within {
        border-color: #FFDE7A !important;
        box-shadow: 0 0 16px rgba(255, 222, 122, 0.5) !important;
        background: rgba(7, 34, 42, 0.98) !important;
    }
    .stTextInput input {
        background: transparent !important;
        border: none !important;
        color: #FFFFFF !important;
        font-size: 0.98rem !important;
        padding: 12px 14px !important;
        font-weight: 500 !important;
    }
    .stTextInput input::placeholder {
        color: rgba(200, 225, 230, 0.65) !important;
        opacity: 1 !important;
    }

    /* Botão Principal Ouro Nobre Vibrante */
    .stButton > button {
        background: linear-gradient(135deg, #FFDE7A 0%, #D4AF37 50%, #B88928 100%) !important;
        color: #041418 !important;
        font-weight: 800 !important;
        font-size: 0.98rem !important;
        letter-spacing: 1.2px !important;
        text-transform: uppercase !important;
        border: none !important;
        border-radius: 10px !important;
        padding: 12px 24px !important;
        box-shadow: 0 6px 20px rgba(212, 175, 55, 0.45) !important;
        transition: all 0.3s ease !important;
    }
    .stButton > button:hover {
        background: linear-gradient(135deg, #FFF0B8 0%, #FFDE7A 50%, #C9972E 100%) !important;
        box-shadow: 0 8px 28px rgba(212, 175, 55, 0.65) !important;
        transform: translateY(-2px) !important;
    }
    </style>
    """)
    
    col_art, col_auth = st.columns([1, 1.15], gap="large")
    
    with col_art:
        import base64
        poster_b64 = ""
        poster_file = "manu_avatar.jpg" if os.path.exists("manu_avatar.jpg") else "logo_economyconty.jpg"
        if os.path.exists(poster_file):
            with open(poster_file, "rb") as f_img:
                poster_b64 = base64.b64encode(f_img.read()).decode("utf-8")
                
        if poster_b64:
            st.html(f"""
            <div class="notranslate" translate="no" style="display: flex; justify-content: center; align-items: center; height: 100%;">
                <img src="data:image/jpeg;base64,{poster_b64}" 
                     alt="Manu EconomyContY" 
                     style="max-height: 575px; width: auto; max-width: 100%; border-radius: 18px; border: 1.5px solid rgba(194, 163, 92, 0.45); box-shadow: 0 20px 48px rgba(0,0,0,0.6); object-fit: contain;" />
            </div>
            """)
        elif os.path.exists("logo_economyconty.jpg"):
            st.image("logo_economyconty.jpg", use_container_width=True)
            
    with col_auth:
        st.html("""
        <div class="notranslate" translate="no" style="margin-bottom: 16px;">
            <div style="display: inline-flex; align-items: center; gap: 6px; background: rgba(212, 175, 55, 0.18); border: 1px solid rgba(212, 175, 55, 0.45); border-radius: 20px; padding: 5px 14px; margin-bottom: 10px;">
                <span style="color: #ECC86A; font-size: 0.78rem; font-weight: 800; letter-spacing: 1.2px; text-transform: uppercase;">Portal Executivo • Ambiente Demo & Comercial</span>
            </div>
            <div style="color: #FFFFFF; font-family: 'Cinzel', serif; font-size: 1.65rem; font-weight: 700; letter-spacing: 0.8px; line-height: 1.2; text-shadow: 0 2px 10px rgba(0,0,0,0.5);">
                Finanças & Consultoria
            </div>
            <div style="color: #B5D5DC; font-size: 0.88rem; margin-top: 5px; font-weight: 500;">
                Plataforma Comercial de Inteligência Contábil & Gestão Patrimonial
            </div>
        </div>
        """)
        
        tab_login, tab_cadastro = st.tabs(["🔐 Entrar na Conta", "✨ Criar Nova Conta"])
        
        with tab_login:
            identificador = st.text_input("Usuário ou E-mail", key="login_user", placeholder="ex: demo ou seu@email.com")
            senha = st.text_input("Senha", type="password", key="login_pass", placeholder="••••••••")
            
            if st.button("ACESSAR PLATAFORMA", use_container_width=True):
                if not identificador or not senha:
                    st.warning("Preencha todos os campos para entrar.")
                else:
                    sucesso, uid, nome, plano = verificar_credenciais(identificador, senha)
                    if sucesso:
                        st.session_state.usuario_logado = True
                        st.session_state.user_id = uid
                        st.session_state.nome_usuario = nome
                        st.session_state.plano_usuario = plano
                        st.rerun()
                    else:
                        st.error("Credenciais inválidas. Verifique seu usuário e senha.")
                        
            st.html("""
            <div class="notranslate" translate="no" style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; margin-top: 16px; margin-bottom: 12px;">
                <div style="background: rgba(7, 30, 36, 0.75); border: 1px solid rgba(212, 175, 55, 0.28); border-radius: 10px; padding: 9px 5px; text-align: center;">
                    <div style="font-size: 1.05rem;">🔒</div>
                    <div style="font-size: 0.72rem; color: #ECC86A; font-weight: 700; margin-top: 3px;">Criptografia</div>
                    <div style="font-size: 0.65rem; color: #A3C9D0;">Segurança Bancária</div>
                </div>
                <div style="background: rgba(7, 30, 36, 0.75); border: 1px solid rgba(212, 175, 55, 0.28); border-radius: 10px; padding: 9px 5px; text-align: center;">
                    <div style="font-size: 1.05rem;">📸</div>
                    <div style="font-size: 0.72rem; color: #ECC86A; font-weight: 700; margin-top: 3px;">Scanner IA</div>
                    <div style="font-size: 0.65rem; color: #A3C9D0;">Leitura de Cupons</div>
                </div>
                <div style="background: rgba(7, 30, 36, 0.75); border: 1px solid rgba(212, 175, 55, 0.28); border-radius: 10px; padding: 9px 5px; text-align: center;">
                    <div style="font-size: 1.05rem;">📊</div>
                    <div style="font-size: 0.72rem; color: #ECC86A; font-weight: 700; margin-top: 3px;">Banco Central</div>
                    <div style="font-size: 0.65rem; color: #A3C9D0;">Dados Oficiais SGS</div>
                </div>
            </div>

            <div class="notranslate" translate="no" style="background: rgba(8, 38, 46, 0.85); border: 1.5px solid rgba(212, 175, 55, 0.4); border-radius: 10px; padding: 12px 16px; font-size: 0.82rem; color: #E5EEF0; text-align: center; box-shadow: 0 4px 18px rgba(0,0,0,0.35);">
                👑 <b style="color: #ECC86A;">Conta de Demonstração Rápida:</b><br>
                <div style="margin-top: 5px;">
                    Usuário: <code style="color: #041418; background: #ECC86A; padding: 2px 7px; border-radius: 5px; font-weight: 800; font-size: 0.85rem;">demo</code> &nbsp;|&nbsp; Senha: <code style="color: #041418; background: #ECC86A; padding: 2px 7px; border-radius: 5px; font-weight: 800; font-size: 0.85rem;">123456</code>
                </div>
            </div>

            <div class="notranslate" translate="no" style="text-align: center; margin-top: 14px; font-size: 0.74rem; color: #9CA3AF;">
                <span style="color: #C2A35C; font-weight: 700; letter-spacing: 0.5px;">EconomyContY</span> • Inteligência Contábil & Gestão Financeira<br>
                <span style="font-size: 0.70rem; color: #6B7280;">© Todos os direitos reservados • Emanuela Freires</span>
            </div>
            """)
            with st.expander("📜 Consultar Termo de Uso, Segurança de Dados (LGPD) e Regras de Teste", expanded=False):
                st.markdown(TERMO_ACEITE_LGPD_TEXTO)
            
        with tab_cadastro:
            novo_nome = st.text_input("Seu Nome Completo", key="cad_nome", placeholder="Ex: Emanuela Freires")
            novo_user = st.text_input("Escolha um Nome de Usuário", key="cad_user", placeholder="Ex: emanuela")
            novo_email = st.text_input("Seu E-mail", key="cad_email", placeholder="Ex: emanuela@contabilidade.com")
            nova_senha = st.text_input("Crie uma Senha (mín. 6 dígitos)", type="password", key="cad_pass", placeholder="••••••••")
            
            with st.expander("📜 Ler Termo de Aceite, Segurança de Dados (LGPD) e Regras de Teste (Obrigatório)", expanded=False):
                st.markdown(TERMO_ACEITE_LGPD_TEXTO)
                
            aceite_lgpd = st.checkbox(
                "✅ Li e concordo com os Termos de Uso, Diretrizes de Segurança de Dados (LGPD) e Regras do Programa de Testes do EconomyContY.",
                value=False,
                key="cad_aceite_lgpd"
            )
            
            if st.button("CRIAR MINHA CONTA", use_container_width=True):
                if not novo_nome or not novo_user or not nova_senha:
                    st.warning("Preencha nome, usuário e senha para cadastrar.")
                elif not aceite_lgpd:
                    st.warning("⚠️ Para criar sua conta e participar dos testes, é obrigatório ler e marcar o aceite do Termo de Segurança de Dados (LGPD) e Regras de Teste.")
                else:
                    ok, msg, uid = cadastrar_usuario(novo_user, novo_nome, novo_email, nova_senha, aceitou_termos=aceite_lgpd)
                    if ok:
                        st.success(msg)
                    else:
                        st.error(msg)
                        
    st.stop()

# ==============================================================================
# ÁREA LOGADA DO USUÁRIO
# ==============================================================================
user_id = st.session_state.user_id
nome_usuario = st.session_state.nome_usuario

# Barra Lateral Executiva
with st.sidebar:
    import base64
    if os.path.exists("logo_economyconty.jpg"):
        st.image("logo_economyconty.jpg", use_container_width=True)
        
    st.markdown("""
    <div style="text-align: center; margin-top: 4px; margin-bottom: 12px;">
        <span class="brand-badge notranslate" translate="no" style="font-size: 0.72rem; letter-spacing: 0.08em; text-transform: uppercase;">
            EconomyContY • Finance & Consulting
        </span>
    </div>
    """, unsafe_allow_html=True)
    
    manu_face_b64 = ""
    if os.path.exists("manu_face.png"):
        with open("manu_face.png", "rb") as f_img:
            manu_face_b64 = base64.b64encode(f_img.read()).decode("utf-8")
            
    if manu_face_b64:
        avatar_html = f'<img src="data:image/png;base64,{manu_face_b64}" style="width: 44px; height: 44px; border-radius: 50%; border: 2px solid #C2A35C; object-fit: cover; margin-right: 12px; box-shadow: 0 0 10px rgba(194,163,92,0.35);" />'
    else:
        avatar_html = '<div style="width: 44px; height: 44px; border-radius: 50%; background: #C2A35C; color: #193035; display: flex; align-items: center; justify-content: center; font-weight: 700; margin-right: 12px;">EC</div>'
        
    st.markdown(f"""
    <div class="notranslate" translate="no" style="background: rgba(15, 26, 42, 0.7); border: 1px solid rgba(194, 163, 92, 0.25); border-radius: 12px; padding: 10px 14px; margin-bottom: 14px; display: flex; align-items: center;">
        {avatar_html}
        <div>
            <div style="font-weight: 700; font-size: 0.88rem; color: #F3E5AB;">{nome_usuario}</div>
            <div style="font-size: 0.72rem; color: #9CA3AF;">Plano: {st.session_state.plano_usuario}</div>
            <div style="font-size: 0.68rem; color: #C2A35C; margin-top: 2px;">✨ Manu EconomyContY Ativa</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # --- LANÇAMENTO RÁPIDO EM 1 CLIQUE (ESTILO APPS NOTA 5 GOOGLE PLAY) ---
    with st.popover("⚡ + Lançamento Rápido", use_container_width=True):
        st.markdown("<p style='font-size:0.85rem; font-weight:800; color:#FFDE7A; margin-bottom:4px;'>⚡ Registro Instantâneo (1 Clique)</p>", unsafe_allow_html=True)
        q_tipo = st.radio("Natureza:", ["Despesa", "Receita"], horizontal=True, key="quick_tipo_sb")
        opcoes_q_sub = SUBCATEGORIAS_DESPESAS if q_tipo == "Despesa" else SUBCATEGORIAS_RECEITAS
        q_sub = st.selectbox("Categoria com Ícone:", opcoes_q_sub, key="quick_sub_sb")
        q_sonho_id = None
        if q_tipo == "Despesa" and "Patrimônio" in q_sub:
            df_sonhos_sb = listar_sonhos(user_id)
            if not df_sonhos_sb.empty:
                opcoes_sonhos_sb = {"Não vincular a Caixinha": None}
                for _, rs in df_sonhos_sb.iterrows():
                    opcoes_sonhos_sb[f"🎯 {rs['titulo']} (Falta {max(100.0 - (float(rs['valor_atual'])/max(float(rs['valor_alvo']),0.01)*100.0), 0.0):.1f}%)"] = int(rs['id'])
                escolha_sb = st.selectbox("🎯 Destinar para qual Caixinha / Sonho?", list(opcoes_sonhos_sb.keys()), key="quick_sonho_sb")
                q_sonho_id = opcoes_sonhos_sb[escolha_sb]
        q_desc = st.text_input("Descrição:", placeholder="Ex: Almoço, Uber, Supermercado...", key="quick_desc_sb")
        q_col1, q_col2 = st.columns(2)
        with q_col1:
            q_val = st.number_input("Valor (R$):", min_value=0.0, step=10.0, format="%.2f", key="quick_val_sb")
        with q_col2:
            q_banco = st.text_input("Conta/Banco:", value="Itaú", key="quick_banco_sb")
        q_col3, q_col4 = st.columns(2)
        with q_col3:
            q_data = st.date_input("Data:", value=date.today(), key="quick_data_sb")
        with q_col4:
            q_status = st.selectbox("Status:", ["Pago", "Pendente"], index=0, key="quick_status_sb")
        
        if st.button("💾 Salvar Agora", type="primary", use_container_width=True, key="btn_quick_save_sb"):
            if q_val <= 0:
                st.warning("Informe um valor maior que R$ 0,00.")
            else:
                import uuid
                desc_final_q = q_desc.strip() if q_desc.strip() else q_sub.split(" ", 1)[-1]
                cat_503020_q = MAPA_SUBCATEGORIA_503020.get(q_sub, "Desejo (30%)" if q_tipo == "Despesa" else "Renda (Não se aplica)")
                ded_q = 1 if q_sub in ["💊 Saúde & Farmácia", "🎓 Educação & Cursos"] else 0
                dt_q_str = q_data.strftime("%Y-%m-%d")
                adicionar_lancamento(
                    user_id=user_id,
                    tipo=q_tipo,
                    descricao=desc_final_q,
                    valor=q_val,
                    data_vencimento=dt_q_str,
                    categoria=cat_503020_q,
                    subcategoria=q_sub,
                    conta=q_banco.strip() or "Itaú",
                    status=q_status,
                    protocolo=f"FAST-{str(uuid.uuid4())[:6].upper()}",
                    data_pagamento=dt_q_str,
                    tributavel=0,
                    dedutivel=ded_q,
                    origem="Lançamento Rápido"
                )
                if q_sonho_id is not None:
                    info_ap = aportar_sonho(user_id, q_sonho_id, q_val, registrar_lancamento=False, banco=q_banco.strip() or "Itaú", data_aporte=dt_q_str)
                    if info_ap:
                        st.session_state["alerta_aporte_sonho"] = info_ap
                        st.toast(
                            f"🎯 Aplicação na Caixinha '{info_ap['titulo']}'! "
                            f"Você já atingiu {info_ap['pct_atingido']:.1f}% — Falta apenas {info_ap['pct_falta']:.1f}% (R$ {info_ap['valor_falta']:,.2f}) para realizar seu sonho!"
                        )
                else:
                    st.toast(f"✅ {q_sub}: R$ {q_val:,.2f} salvo com sucesso!")
                st.rerun()

    st.markdown("---")
    st.markdown("<p style='font-size:0.75rem; font-weight:700; color:#C2A35C; text-transform:uppercase; letter-spacing:1px; margin-bottom:6px;'>Navegação Executiva</p>", unsafe_allow_html=True)
    menu = st.radio(
        "Navegação",
        [
            "🏠 Painel Principal",
            "✍️ Lançamentos",
            "📊 Extrato e Alertas",
            "💳 Faturas de Cartão",
            "💼 Meu Patrimônio",
            "🎯 Sonhos & Caixinhas",
            "⚙️ Minha Conta"
        ],
        index=0,
        label_visibility="collapsed"
    )
    
    st.markdown("---")
    if st.button("🚪 Sair do Aplicativo", use_container_width=True):
        st.session_state.usuario_logado = False
        st.session_state.user_id = None
        st.session_state.nome_usuario = ""
        st.rerun()

user_id = st.session_state.user_id
nome_usuario = st.session_state.nome_usuario

# Notificação persistente de evolução de Sonho / Caixinha quando houver aporte recente
if st.session_state.get("alerta_aporte_sonho"):
    info_s = st.session_state.pop("alerta_aporte_sonho")
    if info_s["pct_falta"] <= 0:
        st.balloons()
        st.success(
            f"🏆 **PARABÉNS! SONHO 100% REALIZADO!** Com a aplicação de **R$ {info_s['valor_aporte']:,.2f}**, "
            f"sua Caixinha **{info_s['titulo']}** chegou a **R$ {info_s['novo_valor']:,.2f}** (Meta: R$ {info_s['valor_alvo']:,.2f})! **Falta 0,0%!**"
        )
    else:
        st.info(
            f"🎯 **Sinalizador de Sonho ({info_s['titulo']}):** Aplicação de **R$ {info_s['valor_aporte']:,.2f}** registrada na caixinha! "
            f"Saldo acumulado: **R$ {info_s['novo_valor']:,.2f}** ({info_s['pct_atingido']:.1f}% concluído) • "
            f"⏳ **Falta {info_s['pct_falta']:.1f}% (R$ {info_s['valor_falta']:,.2f}) para atingir seu sonho!**"
        )

# ------------------------------------------------------------------------------
# ROTEAMENTO EXECUTIVO MULTI-TENANT (ECONOMYCONTY COMERCIAL & DEMO)
# ------------------------------------------------------------------------------
if "Painel Principal" in menu:
    from modules.painel import render_painel_principal
    render_painel_principal(user_id=user_id, nome_usuario=nome_usuario, manu_face_b64=manu_face_b64)

elif "Lançamentos" in menu:
    from modules.lancamentos import render_lancamentos
    render_lancamentos(user_id=user_id, nome_usuario=nome_usuario, manu_face_b64=manu_face_b64)

elif "Extrato" in menu:
    from modules.extrato import render_extrato
    render_extrato(user_id=user_id, nome_usuario=nome_usuario, manu_face_b64=manu_face_b64)

elif "Fatura" in menu:
    from modules.faturas import render_faturas
    render_faturas(user_id=user_id, nome_usuario=nome_usuario, manu_face_b64=manu_face_b64)

elif "Patrimônio" in menu:
    from modules.patrimonio import render_patrimonio
    render_patrimonio(user_id=user_id, nome_usuario=nome_usuario, manu_face_b64=manu_face_b64)

elif "Sonhos" in menu:
    from modules.sonhos import render_sonhos
    render_sonhos(user_id=user_id, nome_usuario=nome_usuario, manu_face_b64=manu_face_b64)

elif "Minha Conta" in menu:
    st.markdown("<h2 class='brand-title' style='margin-bottom: 5px;'>Minha Conta & Segurança</h2>", unsafe_allow_html=True)
    st.markdown("<p style='color: #94A3B8; margin-bottom: 25px;'>Gerencie seus dados de acesso e preferências do aplicativo.</p>", unsafe_allow_html=True)
    
    col_p1, col_p2 = st.columns(2)
    with col_p1:
        st.markdown(f"""
            <div class='kpi-card' style='margin-bottom: 20px;'>
                <div class='kpi-label'>Perfil do Usuário</div>
                <div style='font-size: 1.2rem; font-weight: 700; color: #FFFFFF;'>{nome_usuario}</div>
                <div style='color: #94A3B8; font-size: 0.85rem; margin-top: 4px;'>ID da Conta: #{user_id}</div>
                <div style='color: #D4AF37; font-size: 0.85rem; margin-top: 4px;'>Plano Atual: {st.session_state.plano_usuario}</div>
            </div>
        """, unsafe_allow_html=True)
        
        st.markdown("#### 🤖 Inteligência Artificial (Visão de Cupom)")
        with st.expander("Configurar Chave Google Gemini API (Opcional)", expanded=False):
            st.markdown("<p style='font-size: 0.82rem; color: #94A3B8;'>Para habilitar leitura multimodal em tempo real com precisão máxima pelo modelo Gemini 1.5 Flash, insira sua chave gratuita do Google AI Studio.</p>", unsafe_allow_html=True)
            gemini_key_input = st.text_input("Chave Gemini API", value=st.session_state.get("gemini_api_key", ""), type="password", placeholder="AIzaSy...")
            if st.button("SALVAR CHAVE DE IA"):
                st.session_state.gemini_api_key = gemini_key_input.strip()
                st.success("Chave de IA configurada com sucesso!")
        
    with col_p2:
        st.markdown("#### 🔒 Alterar Senha")
        with st.form("form_change_pass"):
            senha_atual = st.text_input("Senha Atual", type="password")
            nova_senha = st.text_input("Nova Senha (mín. 6 dígitos)", type="password")
            conf_senha = st.text_input("Confirmar Nova Senha", type="password")
            
            if st.form_submit_button("ATUALIZAR SENHA", use_container_width=True):
                if nova_senha != conf_senha:
                    st.error("A confirmação da senha não confere.")
                else:
                    ok, msg = alterar_senha(user_id, senha_atual, nova_senha)
                    if ok:
                        st.success(msg)
                    else:
                        st.error(msg)

    st.markdown("---")
    st.markdown("#### 🛡️ Segurança de Dados (LGPD) & Termo de Aceite do Programa de Testes")
    st.markdown("""
        <div style='background: rgba(16, 185, 129, 0.1); border: 1px solid rgba(16, 185, 129, 0.4); border-radius: 10px; padding: 12px 16px; margin-bottom: 12px; font-size: 0.86rem; color: #E2EEF0;'>
            ✅ <b>Status de Conformidade:</b> Termo de Uso, Privacidade de Dados (LGPD — Lei nº 13.709/2018) e Regras de Teste Beta aceitos e ativos para esta conta. Seus dados são isolados por <code>user_id</code> e protegidos com hash criptográfico <code>SHA-256 + Salt</code>.
        </div>
    """, unsafe_allow_html=True)
    with st.expander("📜 Visualizar Termo Completo de Aceite, Privacidade (LGPD) e Regras de Teste", expanded=False):
        st.markdown(TERMO_ACEITE_LGPD_TEXTO)
