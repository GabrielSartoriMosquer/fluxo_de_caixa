import streamlit as st
from utils.session import init_session_state, refresh_data
import time

# 1. Configuração da Página 
st.set_page_config(page_title="Fluxo de Caixa - Farmácia", page_icon="🌿", layout="wide")

# Autenticação
def check_password():
    if 'logged_in' not in st.session_state:
        st.session_state['logged_in'] = False

    if not st.session_state['logged_in']:
        st.title("🔐 Acesso Restrito - Farmácia")
        senha = st.text_input("Digite a senha de acesso", type="password")
        
        if st.button("Entrar"):
            if senha == st.secrets['APP_PASSWORD']:
                st.session_state['logged_in'] = True
                st.success("Login realizado!")
                time.sleep(0.5)
                st.rerun()
            else:
                st.error("Senha incorreta.")
        return False
    return True

if not check_password():
    st.stop()

# 2. Inicializa Serviços e Estado
init_session_state()
refresh_data()

# 3. Importação das Views
from views import home, vendas, estoque, agendamento, cadastros, dashboard

# 4. Navegação Lateral
st.sidebar.title("Menu Principal")

menu_options = {
    "inicio":       {"title": "🏠 Início",           "module": home},
    "vendas":       {"title": "💰 Vender",           "module": vendas},
    "repor_estoque":{"title": "📦 Repor Estoque",    "module": estoque},
    "agendamento":  {"title": "🗓️ Marcar Horário",  "module": agendamento},
    "cadastros":    {"title": "📝 Cadastros",        "module": cadastros},
    "visualizacao": {"title": "🔍 Visualização",     "module": dashboard}
}

selection = st.sidebar.radio(
    "O que a senhora deseja fazer?", 
    list(menu_options.keys()), 
    format_func=lambda x: menu_options[x]["title"]
)

if st.sidebar.button("🔄 Atualizar Tudo"):
    st.session_state['refresh'] = True
    st.rerun()

# 5. Renderização da Tela Escolhida
module = menu_options[selection]["module"]
module.render_view()