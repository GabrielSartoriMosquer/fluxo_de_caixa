import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

def render_view():
    st.title("📊 Dashboard Estratégico")
    st.write("Visão geral de performance, financeiro e operacional.")

    # 1. CARREGAMENTO E PREPARAÇÃO DE DADOS
    # Recuperamos os DataFrames da sessão com segurança
    df_trans = st.session_state.get('transacoes', pd.DataFrame())
    df_cli = st.session_state.get('clientes', pd.DataFrame())
    df_ag = st.session_state.get('agendamentos', pd.DataFrame())
    
    # Garantir tipos de data
    if not df_trans.empty and 'data_transacao' in df_trans.columns:
        df_trans['data_transacao'] = pd.to_datetime(df_trans['data_transacao'])
    
    if not df_ag.empty and 'data_agendamento' in df_ag.columns:
        df_ag['data_agendamento'] = pd.to_datetime(df_ag['data_agendamento'])

    # --- 2. CÁLCULO DE KPIS (INDICADORES) ---
    faturamento_total = df_trans['valor_total'].sum() if not df_trans.empty else 0.0
    qtd_vendas = len(df_trans)
    ticket_medio = (faturamento_total / qtd_vendas) if qtd_vendas > 0 else 0.0
    
    # Cálculo de novos clientes (mês atual)
    novos_clientes = 0
    if not df_cli.empty and 'created_at' in df_cli.columns:
        df_cli['created_at'] = pd.to_datetime(df_cli['created_at'])
        mes_atual = datetime.now().month
        novos_clientes = len(df_cli[df_cli['created_at'].dt.month == mes_atual])

    # --- 3. EXIBIÇÃO DOS KPIS (LINHA DO TOPO) ---
    # Container para destacar os números principais
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("💰 Faturamento Total", f"R$ {faturamento_total:,.2f}")
    c2.metric("🎫 Ticket Médio", f"R$ {ticket_medio:,.2f}")
    c3.metric("🛒 Total de Vendas", qtd_vendas)
    c4.metric("👥 Novos Clientes (Mês)", novos_clientes)

    st.divider()

    # --- 4. GRÁFICOS PRINCIPAIS ---
    col_g1, col_g2 = st.columns([2, 1])

    with col_g1:
        st.subheader("📈 Evolução de Vendas")
        if not df_trans.empty:
            # Agrupa por SEMANA ('W') para evitar gráfico esburacado
            vendas_tempo = df_trans.set_index('data_transacao').resample('W')['valor_total'].sum().reset_index()
            
            fig_evolucao = px.area(
                vendas_tempo, 
                x='data_transacao', 
                y='valor_total',
                title="Faturamento Semanal",
                labels={'data_transacao': 'Período', 'valor_total': 'Faturamento (R$)'},
                color_discrete_sequence=['#00B4D8'] # Azul moderno
            )
            fig_evolucao.update_layout(hovermode="x unified")
            st.plotly_chart(fig_evolucao, use_container_width=True)
        else:
            st.info("Sem dados de vendas para gerar gráfico.")

    with col_g2:
        st.subheader("💳 Meios de Pagamento")
        if not df_trans.empty:
            pagamentos = df_trans['pagamento'].value_counts().reset_index()
            pagamentos.columns = ['Meio', 'Qtd']
            
            # CORREÇÃO DO ERRO: Usamos px.pie com o parâmetro 'hole' para fazer o donut
            fig_pizza = px.pie(
                pagamentos, 
                values='Qtd', 
                names='Meio', 
                hole=0.5, # Isso transforma a pizza em rosca
                color_discrete_sequence=px.colors.sequential.RdBu
            )
            fig_pizza.update_traces(textposition='inside', textinfo='percent+label')
            fig_pizza.update_layout(showlegend=False)
            st.plotly_chart(fig_pizza, use_container_width=True)
        else:
            st.info("Sem dados.")

    # --- 5. GRÁFICOS SECUNDÁRIOS ---
    col_g3, col_g4 = st.columns(2)

    with col_g3:
        st.subheader("💇‍♀️ Top Serviços")
        if not df_ag.empty:
            top_serv = df_ag['Serviço'].value_counts().head(5).reset_index()
            top_serv.columns = ['Serviço', 'Agendamentos']
            
            fig_bar = px.bar(
                top_serv, 
                x='Agendamentos', 
                y='Serviço', 
                orientation='h',
                text='Agendamentos',
                color='Agendamentos'
            )
            fig_bar.update_layout(yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig_bar, use_container_width=True)
        else:
            st.info("Agenda vazia.")

    with col_g4:
        st.subheader("🏆 Ranking Equipe")
        if not df_ag.empty:
            # Conta atendimentos concluídos por profissional
            rank = df_ag[df_ag['status'] == 'Concluído']['Profissional'].value_counts().reset_index()
            rank.columns = ['Profissional', 'Atendimentos']
            
            if not rank.empty:
                # Tabela estilizada com barra de progresso
                st.dataframe(
                    rank,
                    column_config={
                        "Atendimentos": st.column_config.ProgressColumn(
                            "Performance",
                            format="%d",
                            min_value=0,
                            max_value=int(rank['Atendimentos'].max() * 1.2), # Escala dinâmica
                        ),
                    },
                    use_container_width=True,
                    hide_index=True
                )
            else:
                st.info("Nenhum atendimento concluído ainda.")
        else:
            st.info("Sem dados de equipe.")

    st.divider()

    # --- 6. TABELA DETALHADA ---
    st.subheader("📑 Histórico Recente de Transações")
    
    if not df_trans.empty:
        df_display = df_trans.copy()
        
        if not df_cli.empty:
            df_display['id_cliente'] = df_display['id_cliente'].fillna(0).astype(int)
            df_cli['id'] = df_cli['id'].astype(int)
            mapa_nomes = df_cli.set_index('id')['nome'].to_dict()
            df_display['Cliente'] = df_display['id_cliente'].map(mapa_nomes).fillna("Consumidor Final")
        else:
            df_display['Cliente'] = "Consumidor Final"

        df_final = df_display[['data_transacao', 'Cliente', 'valor_total', 'pagamento', 'origem']].copy()
        df_final = df_final.sort_values('data_transacao', ascending=False)
        
        st.dataframe(
            df_final,
            column_config={
                "data_transacao": st.column_config.DatetimeColumn(
                    "Data/Hora",
                    format="D MMM YYYY, HH:mm",
                ),
                "valor_total": st.column_config.NumberColumn(
                    "Valor",
                    format="R$ %.2f"
                ),
                "pagamento": st.column_config.TextColumn(
                    "Pagamento",
                    help="Método utilizado",
                    validate="^(Pix|Dinheiro|Cartão|Boleto)$" 
                ),
                "origem": st.column_config.SelectboxColumn(
                    "Origem",
                    options=["Balcão", "Agendamento"],
                    width="small",
                    disabled=True
                )
            },
            hide_index=True,
            use_container_width=True
        )
    else:
        st.warning("Nenhuma transação registrada no sistema.")