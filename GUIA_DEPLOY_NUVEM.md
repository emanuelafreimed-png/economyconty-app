# 🚀 Guia Passo a Passo: Colocar o EconomyContY na Nuvem e no Celular (24h Online e Gratuito)

Este guia ensina como hospedar a plataforma **EconomyContY** gratuitamente no **Streamlit Community Cloud** para você acessá-la de qualquer lugar (computador, tablet ou celular) e instalá-la como um aplicativo na tela inicial do seu smartphone.

---

## 📦 Pacote de Publicação Pronto
Já preparamos e empacotamos todos os arquivos necessários (código limpo, banco de dados inicial, logos, ícones de celular, manifest PWA e configurações de nuvem) no arquivo:
📁 `financas_app/deploy_nuvem_economyconty.zip` (1.1 MB)

---

## 📝 Passo 1: Criar o Repositório no GitHub (2 minutos)

1. Acesse **[github.com](https://github.com/)** e faça login na sua conta (se não tiver conta, crie uma gratuitamente).
2. No canto superior direito, clique no botão **`+`** e selecione **`New repository`** (Novo Repositório).
3. Preencha as informações:
   - **Repository name:** `economyconty-app`
   - **Visibilidade:** Escolha `Public` (Público) ou `Private` (Privado).
4. Clique no botão verde **`Create repository`**.
5. Na tela seguinte, clique no link **`uploading an existing file`** (enviar arquivos existentes).
6. Descompacte o arquivo `deploy_nuvem_economyconty.zip` e arraste todos os arquivos de dentro dele para a tela do GitHub:
   - `app.py`, `auth.py`, `database.py`, `open_finance.py`, `pdf_extractor.py`, `financas.db`, `requirements.txt`, `.gitignore`, `manifest.json`, pastas e ícones.
7. Role até o final da página e clique no botão verde **`Commit changes`**.

---

## ☁️ Passo 2: Publicar no Streamlit Cloud (1 minuto)

1. Acesse **[share.streamlit.io](https://share.streamlit.io/)** e clique em **`Continue with GitHub`** (autorize a conexão).
2. Na tela inicial, clique no botão **`Create app`** (ou `New app`).
3. Selecione as opções:
   - **Repository:** Escolha o repositório que você acabou de criar (`seu-usuario/economyconty-app`).
   - **Branch:** `main` (ou `master`).
   - **Main file path:** `app.py`.
   - **App URL (Opcional):** Você pode personalizar o link, por exemplo: `https://economyconty.streamlit.app`.
4. Clique no botão azul **`Deploy!`**.
5. Aguarde cerca de 1 minuto enquanto os servidores do Streamlit instalam as dependências e sobem a plataforma.
6. **Pronto!** O sistema estará online 24h por dia na nuvem com certificado de segurança HTTPS (`cadeado verde`).

---

## 📱 Passo 3: Como Instalar no Celular como Aplicativo

Com o link do seu app aberto no navegador do celular (ex: `https://economyconty.streamlit.app`):

### 🍏 No iPhone (Safari):
1. Abra o Safari e acesse o link do seu aplicativo.
2. Toque no ícone de **Compartilhar** (quadrado com uma seta apontando para cima na barra inferior).
3. Role para baixo e selecione **`Adicionar à Tela de Início`**.
4. Toque em **`Adicionar`**.
5. O ícone oficial dourado da **EconomyContY** aparecerá na tela do seu iPhone. Ao clicar nele, o app abrirá em tela cheia, sem barra de endereços do navegador!

### 🤖 No Android (Google Chrome):
1. Abra o Google Chrome e acesse o link do seu aplicativo.
2. Toque nos **três pontinhos** no canto superior direito.
3. Selecione **`Instalar aplicativo`** ou **`Adicionar à tela inicial`**.
4. Toque em **`Instalar`**.
5. O aplicativo da **EconomyContY** será instalado como um app independente no seu celular.

---

## 🔒 Segurança no Acesso Mobile
Ao abrir no celular, o sistema solicitará imediatamente sua senha de segurança configurada:
- **Usuário:** `emanuela`
- **Senha:** `conty2026` (ou a nova senha caso você já tenha alterado).
