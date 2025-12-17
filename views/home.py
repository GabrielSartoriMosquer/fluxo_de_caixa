import streamlit as st
import pandas as pd
from datetime import datetime

def render_view():
    st.title("🏠 Olá, Bem-vinda!")
    st.write(f"Resumo de hoje: **{datetime.now().strftime('%d/%m/%Y')}**")
    
    df_ag = st.session_state.get('agendamentos', pd.DataFrame())
    df_trans = st.session_state.get('transacoes', pd.DataFrame())
    
    hoje_str = datetime.now().strftime('%Y-%m-%d')
    
    vendas_hoje = 0.0
    if not df_trans.empty and 'data_transacao' in df_trans.columns:
        temp_dt = pd.to_datetime(df_trans['data_transacao'])
        mask = temp_dt.dt.strftime('%Y-%m-%d') == hoje_str
        vendas_hoje = df_trans[mask]['valor_total'].sum()

    agendamentos_hoje = pd.DataFrame()
    if not df_ag.empty and 'data_agendamento' in df_ag.columns:
        agendamentos_hoje = df_ag[df_ag['data_agendamento'] == hoje_str]

    # --- MÉTRICAS DO DIA ---
    col1, col2, col3 = st.columns(3)
    
    col1.metric("Caixa do Dia", f"R$ {vendas_hoje:.2f}")
    col2.metric("Agendamentos Hoje", len(agendamentos_hoje))
    
    # Lógica para mostrar o "Próximo Cliente"
    proximo = "Ninguém na fila"
    if not agendamentos_hoje.empty:
        agora = datetime.now().time()
        try:
            agendamentos_hoje['obj_time'] = pd.to_datetime(agendamentos_hoje['horario'], format='%H:%M:%S').dt.time
            futuros = agendamentos_hoje[agendamentos_hoje['obj_time'] > agora].sort_values('obj_time')
            
            if not futuros.empty:
                next_one = futuros.iloc[0]
                proximo = f"{next_one['horario']} - {next_one['Cliente']}"
            else:
                proximo = "Agenda finalizada por hoje"
        except:
            proximo = "-"
            
    col3.metric("Próximo Cliente", proximo)

    st.divider()

    # --- VISUALIZAÇÃO DA AGENDA DO DIA ---
    st.subheader("📅 Sua Agenda Hoje")
    
    if not agendamentos_hoje.empty:
        df_show = agendamentos_hoje[['horario', 'Cliente', 'Serviço', 'Profissional', 'status']].copy()
        df_show = df_show.sort_values('horario')
        
        def highlight_status(val):
            color = '#c8e6c9' if val == 'Concluído' else '#ffcdd2' if val == 'Cancelado' else '#fff9c4'
            return f'background-color: {color}'

        st.dataframe(
            df_show.style.applymap(highlight_status, subset=['status']),
            use_container_width=True,
            hide_index=True
        )
    else:
        st.success("🎉 Agenda livre por hoje! Aproveite para repor estoque ou organizar a loja.")