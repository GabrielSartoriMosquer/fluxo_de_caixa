import streamlit as st
from utils.session import init_session_state, refresh_data

# 1. Configuração da Página (Obrigatório ser a primeira linha executável do Streamlit)
st.set_page_config(page_title="Farmácia das Irmãs", page_icon="🌿", layout="wide")

# 2. Inicializa Serviços e Estado (Banco de Dados)
# Isso garante que a conexão com o Supabase exista antes de qualquer coisa
init_session_state()
refresh_data()

# 3. Importação das Views (Telas)
# Importamos aqui para evitar erros de dependência circular
from views import home, vendas, estoque, agendamento, cadastros, dashboard

# 4. Navegação Lateral
st.sidebar.title("Menu Principal")

# Dicionário que mapeia a chave da URL/Menu para o módulo correspondente
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

# Botão global de atualização
if st.sidebar.button("🔄 Atualizar Tudo"):
    st.session_state['refresh'] = True
    st.rerun()

# 5. Renderização da Tela Escolhida
# O "maestro" delega a responsabilidade de desenhar a tela para o módulo específico
module = menu_options[selection]["module"]
module.render_view()