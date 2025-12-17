import streamlit as st
from components.crud import render_generic_crud
import re

def validate_cpf(cpf):
    cpf_clean = re.sub(r'\D', '', str(cpf))
    if len(cpf_clean) != 11:
        return False, "CPF deve ter 11 números."
    return True, ""

def validate_phone(phone):
    phone_clean = re.sub(r'\D', '', str(phone))
    if len(phone_clean) < 10 or len(phone_clean) > 11:
        return False, "Telefone deve ter 10 ou 11 números (com DDD)."
    return True, ""

def render_view():
    st.title("📝 Meus Cadastros")
    st.write("Aqui você pode adicionar ou editar informações.")

    tab_cli, tab_prod, tab_serv, tab_eq = st.tabs(["👥 Pessoas", "📦 Produtos", "🛠️ Serviços", "👩‍⚕️ Equipe"])

    with tab_cli:
        fields = [
            {'name': 'nome', 'label': 'Nome Completo', 'type': 'text', 'required': True},
            {'name': 'cpf', 'label': 'CPF (apenas números)', 'type': 'text', 'validator': validate_cpf},
            {'name': 'telefone', 'label': 'Telefone (com DDD)', 'type': 'text', 'validator': validate_phone}
        ]
        render_generic_crud('clientes', 'Cliente', fields, st.session_state['clientes'])

    with tab_prod:
        fields = [
            {'name': 'nome', 'label': 'Nome do Produto', 'type': 'text', 'required': True},
            {'name': 'tipo', 'label': 'Tipo (ex: Chá, Óleo)', 'type': 'text'},
            {'name': 'valor_original', 'label': 'Preço (R$)', 'type': 'number', 'step': 0.01},
            {'name': 'estoque', 'label': 'Quantidade em Estoque', 'type': 'number', 'step': 1, 'min': 0}
        ]
        render_generic_crud('produtos', 'Produto', fields, st.session_state['produtos'])

    with tab_serv:
        fields = [
            {'name': 'nome', 'label': 'Nome do Serviço', 'type': 'text', 'required': True},
            {'name': 'valor', 'label': 'Preço (R$)', 'type': 'number', 'step': 0.01},
            {'name': 'duracao_estimada', 'label': 'Tempo (minutos)', 'type': 'number', 'step': 15.0, 'min': 15.0}
        ]
        render_generic_crud('servicos', 'Serviço', fields, st.session_state['servicos'])

    with tab_eq:
        fields = [
            {'name': 'nome', 'label': 'Nome da Pessoa', 'type': 'text', 'required': True},
            {'name': 'observacao', 'label': 'Anotações', 'type': 'textarea'},
            {'name': 'valor', 'label': 'Valor/Comissão (R$)', 'type': 'number', 'step': 0.01},
            {'name': 'ativo', 'label': 'Está trabalhando?', 'type': 'checkbox'}
        ]
        render_generic_crud('atendentes', 'Profissional', fields, st.session_state['atendentes'])