import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, time

def render_view():
    st.title("🔍 Visualização Geral")
    st.write("Veja tudo o que está acontecendo na farmácia.")

    tab_est, tab_vend, tab_ag, tab_func, tab_livre = st.tabs(["📦 Estoque", "💰 Vendas", "📅 Agenda", "👥 Equipe", "🆓 Horários Livres"])

    # --- ABA ESTOQUE ---
    with tab_est:
        st.subheader("📦 Estoque Atual")
        df_prod = st.session_state['produtos']
        if not df_prod.empty:
            df_show = df_prod[['nome', 'tipo', 'valor_original', 'estoque']].copy()
            df_show.columns = ['Produto', 'Tipo', 'Preço (R$)', 'Qtd.']
            st.dataframe(df_show, use_container_width=True, hide_index=True)
            
            baixo = df_prod[df_prod['estoque'] < 5]
            if not baixo.empty:
                st.error(f"⚠️ Atenção! Produtos com pouco estoque: {', '.join(baixo['nome'].tolist())}")
        else:
            st.info("Nenhum produto cadastrado.")

    # --- ABA VENDAS ---
    with tab_vend:
        st.subheader("💰 Histórico de Vendas")
        df_trans = st.session_state['transacoes']
        if not df_trans.empty:
            df_show = df_trans.copy()
            if 'data_transacao' in df_show.columns:
                df_show['Data'] = pd.to_datetime(df_show['data_transacao']).dt.strftime('%d/%m/%Y')
            
            cols_map = {'Data': 'Data', 'valor_total': 'Valor (R$)', 'pagamento': 'Pagamento', 'origem': 'Origem'}
            cols_final = [c for c in cols_map.keys() if c in df_show.columns or c == 'Data']
            
            df_final = df_show[cols_final].rename(columns=cols_map)
            st.dataframe(df_final, use_container_width=True, hide_index=True)
            
            st.divider()
            
            # Gráfico Financeiro (Movido da Agenda para cá)
            if 'valor_total' in df_trans.columns:
                total = df_trans['valor_total'].sum()
                st.metric("Total Vendido (Geral)", f"R$ {total:.2f}")
                
                if 'data_transacao' in df_trans.columns:
                    df_chart = df_trans.copy()
                    df_chart['data_transacao'] = pd.to_datetime(df_chart['data_transacao'])
                    daily = df_chart.groupby('data_transacao')['valor_total'].sum().reset_index()
                    st.plotly_chart(px.bar(daily, x='data_transacao', y='valor_total', title="Vendas por Dia"), use_container_width=True)
        else:
            st.info("Nenhuma venda registrada.")

    # --- ABA AGENDA ---
    with tab_ag:
        st.subheader("📅 Agenda de Serviços")
        df_ag = st.session_state['agendamentos']
        if not df_ag.empty:
            df_show = df_ag.copy()
            if 'data_agendamento' in df_show.columns:
                df_show['Data'] = pd.to_datetime(df_show['data_agendamento']).dt.strftime('%d/%m/%Y')
            
            cols_map = {'Data': 'Data', 'horario': 'Hora', 'Cliente': 'Cliente', 'Serviço': 'Serviço', 'Profissional': 'Profissional', 'status': 'Status'}
            cols_final = [c for c in cols_map.keys() if c in df_show.columns or c == 'Data']
            
            df_final = df_show[cols_final].rename(columns=cols_map)
            st.dataframe(df_final, use_container_width=True, hide_index=True)
        else:
            st.info("Nenhum agendamento.")
            
        # Métricas rápidas de agendamento
        st.metric("Horários Marcados", len(st.session_state['agendamentos']))

    # --- ABA EQUIPE ---
    with tab_func:
        st.subheader("👥 Nossa Equipe")
        df_func = st.session_state['atendentes']
        if not df_func.empty:
             cols_func = [c for c in ['nome', 'observacao', 'valor', 'ativo'] if c in df_func.columns]
             df_show_func = df_func[cols_func].copy()
             rename_map = {'nome': 'Nome', 'observacao': 'Anotações', 'valor': 'Comissão/Valor', 'ativo': 'Ativo?'}
             df_show_func = df_show_func.rename(columns=rename_map)
             st.dataframe(df_show_func, use_container_width=True, hide_index=True)
        else:
             st.info("Ninguém cadastrado na equipe ainda.")

    # --- ABA HORÁRIOS LIVRES ---
    with tab_livre:
        st.subheader("🆓 Consultar Horários Livres")
        dia_sel = st.date_input("Escolha o dia", datetime.now(), format="DD/MM/YYYY")
        
        if dia_sel:
            horarios_possiveis = [time(h, 0) for h in range(8, 19)]
            
            df_ag = st.session_state['agendamentos']
            ocupados = []
            if not df_ag.empty:
                dia_str = dia_sel.strftime('%Y-%m-%d')
                df_dia = df_ag[df_ag['data_agendamento'] == dia_str]
                
                for _, row in df_dia.iterrows():
                    try:
                        h_str = str(row['horario'])
                        h_obj = datetime.strptime(h_str, '%H:%M:%S').time()
                        ocupados.append(h_obj)
                    except:
                        pass
            
            livres = [h for h in horarios_possiveis if h not in ocupados]
            
            if livres:
                st.success(f"Horários livres para {dia_sel.strftime('%d/%m/%Y')}:")
                cols = st.columns(6)
                for i, h in enumerate(livres):
                    cols[i % 6].write(f"✅ {h.strftime('%H:%M')}")
            else:
                st.warning("Não há horários livres neste dia!")