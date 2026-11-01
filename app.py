import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date
import os

from auth import init_auth_db, verificar_credenciais, cadastrar_usuario, alterar_senha
from database import (
    init_db, adicionar_lancamento, excluir_lancamento, 
    carregar_lancamentos, obter_resumo_kpis, processar_e_importar_csv
)
from open_finance import (
    init_open_finance_db, BANCOS_DISPONIVEIS, listar_conexoes_usuario,
    conectar_banco, desconectar_banco, sincronizar_todas_conexoes
)
from ai_scanner import extrair_dados_recibo_ia


# Inicializar Bancos
init_auth_db()
init_db()
init_open_finance_db()

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
    font-size: 0.8rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: #7D5768; /* Ameixa Elegante para subtítulos/apoio */
    margin-bottom: 6px;
}
.kpi-val {
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    font-size: 1.65rem;
    font-weight: 700;
    color: #F9F8F4; /* Marfim para clareza máxima */
}

/* Cores de Destaque Oficiais */
.gold-text { color: #C2A35C !important; }
.gold-intense { color: #B88A2D !important; }
.green-text { color: #10B981 !important; }
.red-text { color: #EF4444 !important; }
.wine-text { color: #4A1728 !important; }
.plum-text { color: #7D5768 !important; }

/* Botões Customizados - Dourado Champagne & Dourado Intenso */
.stButton > button {
    background: linear-gradient(135deg, #C2A35C 0%, #B88A2D 100%) !important;
    color: #193035 !important; /* Texto Verde-Petróleo sobre dourado para contraste premium */
    font-weight: 700 !important;
    border: none !important;
    border-radius: 8px !important;
    padding: 10px 24px !important;
    transition: all 0.3s ease !important;
    letter-spacing: 0.03em !important;
}
.stButton > button:hover {
    box-shadow: 0 0 18px rgba(194, 163, 92, 0.5) !important;
    transform: scale(1.02) !important;
}

/* Abas de Navegação */
.stTabs [data-baseweb="tab-list"] {
    gap: 8px;
    border-bottom: 1px solid rgba(194, 163, 92, 0.25);
}
.stTabs [data-baseweb="tab"] {
    padding: 10px 18px;
    border-radius: 8px 8px 0 0;
    color: #7D5768; /* Ameixa elegante */
    font-weight: 600;
}
.stTabs [aria-selected="true"] {
    background: rgba(194, 163, 92, 0.12) !important;
    color: #C2A35C !important;
    border-bottom: 2px solid #C2A35C !important;
}

/* Badges e Selos */
.brand-badge {
    background: rgba(194, 163, 92, 0.15);
    border: 1px solid rgba(194, 163, 92, 0.4);
    border-radius: 20px;
    padding: 4px 14px;
    font-size: 0.76rem;
    color: #C2A35C;
    font-weight: 600;
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
    .block-container {
        padding-top: max(1.5rem, calc((100vh - 640px) / 2)) !important;
        padding-bottom: 1.5rem !important;
        max-width: 1140px !important;
        margin: 0 auto !important;
    }
    header[data-testid="stHeader"] {
        background: transparent !important;
        height: 2.2rem !important;
    }
    [data-baseweb="tab-list"] {
        background: rgba(15, 23, 42, 0.6) !important;
        border-radius: 10px !important;
        padding: 4px !important;
        border-bottom: none !important;
        margin-bottom: 14px !important;
    }
    [data-baseweb="tab"] {
        border-radius: 8px !important;
        color: #9CA3AF !important;
        font-weight: 600 !important;
        padding: 8px 16px !important;
    }
    [data-baseweb="tab"][aria-selected="true"] {
        background: rgba(194, 163, 92, 0.2) !important;
        color: #F3E5AB !important;
        border-bottom: 2px solid #C2A35C !important;
    }
    .stTextInput input {
        background: rgba(15, 23, 42, 0.85) !important;
        border: 1px solid rgba(194, 163, 92, 0.28) !important;
        color: #F9F8F4 !important;
        border-radius: 8px !important;
        padding: 10px 14px !important;
    }
    .stTextInput input:focus {
        border-color: #C2A35C !important;
        box-shadow: 0 0 12px rgba(194, 163, 92, 0.35) !important;
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
        <div class="notranslate" translate="no" style="margin-bottom: 14px;">
            <div style="display: inline-flex; align-items: center; gap: 6px; background: rgba(194, 163, 92, 0.15); border: 1px solid rgba(194, 163, 92, 0.35); border-radius: 20px; padding: 4px 12px; margin-bottom: 8px;">
                <span style="color: #C2A35C; font-size: 0.75rem; font-weight: 700; letter-spacing: 1.2px; text-transform: uppercase;">Portal Executivo • Ambiente Demo & Comercial</span>
            </div>
            <div style="color: #F9F8F4; font-family: 'Cinzel', serif; font-size: 1.45rem; font-weight: 700; letter-spacing: 0.5px; line-height: 1.2;">
                Finanças & Consultoria
            </div>
            <div style="color: #9CA3AF; font-size: 0.84rem; margin-top: 4px;">
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
            <div class="notranslate" translate="no" style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; margin-top: 14px; margin-bottom: 12px;">
                <div style="background: rgba(15, 26, 42, 0.6); border: 1px solid rgba(194, 163, 92, 0.2); border-radius: 8px; padding: 7px 4px; text-align: center;">
                    <div style="font-size: 0.95rem;">🔒</div>
                    <div style="font-size: 0.70rem; color: #C2A35C; font-weight: 600; margin-top: 2px;">Criptografia</div>
                    <div style="font-size: 0.62rem; color: #9CA3AF;">Segurança Bancária</div>
                </div>
                <div style="background: rgba(15, 26, 42, 0.6); border: 1px solid rgba(194, 163, 92, 0.2); border-radius: 8px; padding: 7px 4px; text-align: center;">
                    <div style="font-size: 0.95rem;">⚡</div>
                    <div style="font-size: 0.70rem; color: #C2A35C; font-weight: 600; margin-top: 2px;">Open Finance</div>
                    <div style="font-size: 0.62rem; color: #9CA3AF;">Multi-Bancos 2026</div>
                </div>
                <div style="background: rgba(15, 26, 42, 0.6); border: 1px solid rgba(194, 163, 92, 0.2); border-radius: 8px; padding: 7px 4px; text-align: center;">
                    <div style="font-size: 0.95rem;">📊</div>
                    <div style="font-size: 0.70rem; color: #C2A35C; font-weight: 600; margin-top: 2px;">Banco Central</div>
                    <div style="font-size: 0.62rem; color: #9CA3AF;">Dados Oficiais SGS</div>
                </div>
            </div>

            <div class="notranslate" translate="no" style="background: rgba(212, 175, 55, 0.08); border: 1px solid rgba(212, 175, 55, 0.25); border-radius: 8px; padding: 10px 14px; font-size: 0.78rem; color: #D1D5DB; text-align: center;">
                👑 <b>Conta de Demonstração Rápida:</b><br>
                Usuário: <code style="color: #F3E5AB; background: rgba(0,0,0,0.3); padding: 1px 5px; border-radius: 4px; font-weight: 600;">demo</code> | Senha: <code style="color: #F3E5AB; background: rgba(0,0,0,0.3); padding: 1px 5px; border-radius: 4px; font-weight: 600;">123456</code>
            </div>

            <div class="notranslate" translate="no" style="text-align: center; margin-top: 14px; font-size: 0.74rem; color: #9CA3AF;">
                <span style="color: #C2A35C; font-weight: 700; letter-spacing: 0.5px;">EconomyContY</span> • Inteligência Contábil & Gestão Financeira<br>
                <span style="font-size: 0.70rem; color: #6B7280;">© Todos os direitos reservados • Emanuela Freires</span>
            </div>
            """)
            
        with tab_cadastro:
            novo_nome = st.text_input("Seu Nome Completo", key="cad_nome", placeholder="Ex: Emanuela Freires")
            novo_user = st.text_input("Escolha um Nome de Usuário", key="cad_user", placeholder="Ex: emanuela")
            novo_email = st.text_input("Seu E-mail", key="cad_email", placeholder="Ex: emanuela@contabilidade.com")
            nova_senha = st.text_input("Crie uma Senha (mín. 6 dígitos)", type="password", key="cad_pass", placeholder="••••••••")
            
            if st.button("CRIAR MINHA CONTA", use_container_width=True):
                if not novo_nome or not novo_user or not nova_senha:
                    st.warning("Preencha nome, usuário e senha para cadastrar.")
                else:
                    ok, msg, uid = cadastrar_usuario(novo_user, novo_nome, novo_email, nova_senha)
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
    
    st.markdown("---")
    st.markdown("<p style='font-size:0.75rem; font-weight:700; color:#C2A35C; text-transform:uppercase; letter-spacing:1px; margin-bottom:6px;'>Navegação Executiva</p>", unsafe_allow_html=True)
    menu = st.radio(
        "Navegação",
        [
            "🏠 Painel Principal",
            "✍️ Lançamentos",
            "📊 Extrato e Alertas",
            "📄 Leitor de Rendas (PDF)",
            "🤝 Conciliação Bancária",
            "🔄 Open Finance (Bancos)",
            "💳 Faturas de Cartão",
            "💼 Meu Patrimônio",
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

elif "Leitor" in menu:
    from modules.leitor_rendas import render_leitor_rendas
    render_leitor_rendas(user_id=user_id, nome_usuario=nome_usuario, manu_face_b64=manu_face_b64)

elif "Conciliação" in menu:
    from modules.conciliacao import render_conciliacao
    render_conciliacao(user_id=user_id, nome_usuario=nome_usuario, manu_face_b64=manu_face_b64)

elif "Open Finance" in menu:
    st.markdown("""
    <div style="margin-bottom: 1.5rem; padding-bottom: 0.8rem; border-bottom: 1px solid rgba(212, 175, 55, 0.2);">
        <h1 style="margin: 0; font-size: 2rem; font-weight: 800; background: linear-gradient(90deg, #F9FAFB, #D4AF37); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
            🔄 Open Finance Brasil • Sincronização Bancária
        </h1>
        <p style="margin: 4px 0 0 0; color: #9CA3AF; font-size: 0.9rem;">
            Conecte suas contas bancárias autorizadas pelo Banco Central para sincronização contínua e automática de transações
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    conexoes = listar_conexoes_usuario(user_id)
    
    col_act1, col_act2 = st.columns([2, 1])
    with col_act1:
        st.markdown(f"#### Instituições Conectadas ({len(conexoes)})")
    with col_act2:
        if st.button("🔄 SINCRONIZAR TODAS AS CONTAS", use_container_width=True):
            with st.spinner("Consultando dados bancários autorizados pelo Open Finance..."):
                novos, msg = sincronizar_todas_conexoes(user_id)
                st.success(msg)
                st.rerun()

    if conexoes.empty:
        st.info("Você ainda não conectou nenhuma instituição bancária. Adicione sua primeira conta abaixo!")
    else:
        for _, row in conexoes.iterrows():
            st.markdown(f"""
                <div style='background: rgba(28, 37, 65, 0.6); border: 1px solid rgba(197, 160, 89, 0.3); border-radius: 10px; padding: 15px; margin-bottom: 12px; display: flex; justify-content: space-between; align-items: center;'>
                    <div>
                        <div style='font-size: 1.1rem; font-weight: 700; color: #FFFFFF;'>{row['nome_exibicao']}</div>
                        <div style='font-size: 0.82rem; color: #94A3B8;'>{row['tipo']} • {row['detalhes_conta']}</div>
                        <div style='font-size: 0.78rem; color: #10B981; margin-top: 4px;'>{row['status']} • Última sincronização: {row['ultima_sincronizacao']}</div>
                    </div>
                </div>
            """, unsafe_allow_html=True)
            if st.button(f"Desconectar {row['nome_exibicao']}", key=f"del_conn_{row['id']}"):
                desconectar_banco(user_id, row["id"])
                st.warning("Instituição desconectada.")
                st.rerun()

    st.markdown("---")
    st.markdown("#### ➕ Conectar Nova Instituição Bancária")
    
    col_b1, col_b2 = st.columns([3, 1])
    with col_b1:
        opcoes_bancos = {b["nome"]: b["codigo"] for b in BANCOS_DISPONIVEIS}
        banco_escolhido_nome = st.selectbox("Selecione a Instituição Financeira", list(opcoes_bancos.keys()))
        banco_codigo = opcoes_bancos[banco_escolhido_nome]
    with col_b2:
        st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
        if st.button("AUTORIZAR CONEXÃO", use_container_width=True):
            ok, msg = conectar_banco(user_id, banco_codigo)
            if ok:
                st.success(msg)
                st.rerun()
            else:
                st.warning(msg)

elif "Fatura" in menu:
    from modules.faturas import render_faturas
    render_faturas(user_id=user_id, nome_usuario=nome_usuario, manu_face_b64=manu_face_b64)

elif "Patrimônio" in menu:
    from modules.patrimonio import render_patrimonio
    render_patrimonio(user_id=user_id, nome_usuario=nome_usuario, manu_face_b64=manu_face_b64)

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
