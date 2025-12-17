import streamlit as st
import pandas as pd
from services.database import DatabaseService

def init_session_state():
    """Inicializa as variáveis de estado e carrega dados se necessário."""
    
    tabelas_padrao = {
        'transacoes': pd.DataFrame(columns=['id', 'created_at', 'data_transacao', 'pagamento', 'origem', 'valor_total', 'id_cliente']),
        'clientes': pd.DataFrame(columns=['id', 'nome', 'cpf', 'telefone']),
        'produtos': pd.DataFrame(columns=['id', 'nome', 'tipo', 'valor_original', 'estoque']),
        'servicos': pd.DataFrame(columns=['id', 'nome', 'valor', 'duracao_estimada']),
        'atendentes': pd.DataFrame(columns=['id', 'nome', 'ativo', 'observacao', 'valor']), 
        'agendamentos': pd.DataFrame(columns=['id', 'data_agendamento', 'horario', 'status', 'Cliente', 'Serviço', 'Profissional']),
        'compras': pd.DataFrame(columns=['id', 'created_at', 'id_produto', 'quantidade', 'valor_total', 'fornecedor', 'data_compra'])
    }

    for key, df_vazio in tabelas_padrao.items():
        if key not in st.session_state:
            st.session_state[key] = df_vazio

    if 'refresh' not in st.session_state:
        st.session_state['refresh'] = True
    
    if 'db_service' not in st.session_state:
        st.session_state['db_service'] = DatabaseService()

def refresh_data():
    """Força atualização dos dados do banco para a sessão."""
    if st.session_state['refresh']:
        db = st.session_state['db_service']
        novos_dados = db.fetch_all_tables()
        if novos_dados:
            for k, v in novos_dados.items():
                if isinstance(v, pd.DataFrame):
                    st.session_state[k] = v
        st.session_state['refresh'] = False