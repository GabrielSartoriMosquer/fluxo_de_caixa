import streamlit as st
import pandas as pd
import plotly.express as px

def render_view():
    st.title("🏠 Bem-vinda à Farmácia!")
    st.write("Aqui está um resumo do dia.")
    
    df_t = st.session_state['transacoes']
    
    if not df_t.empty and 'valor_total' in df_t.columns:
        total = df_t['valor_total'].sum()
        col1, col2 = st.columns(2)
        col1.metric("Dinheiro que entrou", f"R$ {total:.2f}")
        col2.metric("Horários Marcados", len(st.session_state['agendamentos']))
        
        if 'data_transacao' in df_t.columns:
            df_t['data_transacao'] = pd.to_datetime(df_t['data_transacao'])
            daily = df_t.groupby('data_transacao')['valor_total'].sum().reset_index()
            st.plotly_chart(px.bar(daily, x='data_transacao', y='valor_total', title="Vendas por Dia"), use_container_width=True)
    else:
        st.info("Ainda não há dados suficientes para o resumo.")