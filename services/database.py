import streamlit as st
import pandas as pd
from supabase import create_client, Client
from datetime import datetime

class DatabaseService:
    def __init__(self):
        self.client = self._init_connection()

    @staticmethod
    @st.cache_resource
    def _init_connection() -> Client:
        try:
            url = st.secrets["SUPABASE_URL"]
            key = st.secrets["SUPABASE_KEY"]
            return create_client(url, key)
        except Exception as e:
            st.error(f"⚠️ Erro crítico de conexão: {e}")
            return None

    def fetch_all_tables(self):
        """Busca dados de todas as tabelas essenciais."""
        if not self.client: return {}
        
        dados = {}
        tabelas_simples = ['clientes', 'produtos', 'servicos', 'atendentes', 'transacoes', 'compras']
        
        # Tabelas Simples
        for tabela in tabelas_simples:
            try:
                res = self.client.table(tabela).select("*").order('id', desc=True).execute()
                dados[tabela] = pd.DataFrame(res.data)
            except Exception as e:
                print(f"Erro ao buscar {tabela}: {e}")
                dados[tabela] = pd.DataFrame() 

        try:
            res_ag = self.client.table('agendamentos').select("*, clientes(nome), servicos(nome), atendentes(nome)").order('data_agendamento', desc=True).execute()
            dados_flat = []
            for row in res_ag.data:
                r = row.copy()
                r['Cliente'] = row['clientes']['nome'] if row.get('clientes') else 'Desconhecido'
                r['Serviço'] = row['servicos']['nome'] if row.get('servicos') else 'N/A'
                r['Profissional'] = row['atendentes']['nome'] if row.get('atendentes') else 'N/A'
                dados_flat.append(r)
            dados['agendamentos'] = pd.DataFrame(dados_flat)
        except Exception as e:
            print(f"Erro ao buscar agendamentos: {e}")
            dados['agendamentos'] = pd.DataFrame()

        return dados

    def insert(self, table: str, data: dict):
        return self.client.table(table).insert(data).execute()

    def update(self, table: str, data: dict, record_id: int):
        return self.client.table(table).update(data).eq('id', record_id).execute()

    def delete(self, table: str, record_id: int):
        return self.client.table(table).delete().eq('id', record_id).execute()