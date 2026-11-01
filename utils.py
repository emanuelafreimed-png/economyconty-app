import streamlit as st

def render_footer_economyconty():
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

def obter_cor_banco(nome_banco):
    nome = str(nome_banco).lower()
    if 'itaú' in nome or 'itau' in nome:
        return '#D97736' # Laranja Suave / Terracota Nobre Itaú
    elif 'santander' in nome:
        return '#CD5555' # Vermelho Suave / Rubi Acetinado Santander
    elif 'nubank' in nome or 'nu ' in nome or 'roxinho' in nome:
        return '#8A5CB7' # Roxo Ametista Suave Nubank
    elif 'caixa' in nome:
        return '#4682B4' # Azul Ardósia / Steel Blue Caixa
    elif 'brasil' in nome or 'bb' in nome:
        return '#CCA246' # Dourado Ocre / Mostarda Suave Banco do Brasil
    elif 'bradesco' in nome:
        return '#B54D5F' # Carmesim Suave Bradesco
    elif 'inter' in nome:
        return '#D97A3B' # Laranja Suave Inter
    elif 'c6' in nome:
        return '#64748B' # Slate Steel C6 Bank
    elif 'inss' in nome:
        return '#4E89AE' # Azul Previdência Muted
    else:
        return '#C5A556' # Dourado Suave EconomyContY padrão

def formatar_moeda_br(v):
    return f"R$ {float(v):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
