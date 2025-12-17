import streamlit as st
from datetime import datetime, time, timedelta
import pandas as pd

def render_view():
    st.title("🗓️ Marcar um Horário")
    
    db = st.session_state['db_service']
    
    # Carrega DataFrames da sessão
    df_cli = st.session_state['clientes']
    df_serv = st.session_state['servicos']
    df_prof = st.session_state['atendentes']
    
    # Cria dicionários para os Selectboxes (ID -> Nome/Valor)
    cli_dict = df_cli.set_index('id')['nome'].to_dict() if not df_cli.empty else {}
    serv_dict = df_serv.set_index('id')['nome'].to_dict() if not df_serv.empty else {}
    # Dicionário de duração para calcular horários de fim
    duracao_dict = df_serv.set_index('id')['duracao_estimada'].to_dict() if not df_serv.empty else {}
    prof_dict = df_prof.set_index('id')['nome'].to_dict() if not df_prof.empty else {}
    
    # --- 1. FILTROS ---
    c_filtro1, c_filtro2 = st.columns(2)
    dt_sel = c_filtro1.date_input("Filtrar Data", datetime.now())
    
    prof_id = None
    if prof_dict:
        prof_id = c_filtro2.selectbox("Filtrar Profissional", list(prof_dict.keys()), format_func=lambda x: prof_dict[x])
    else:
        c_filtro2.warning("Cadastre profissionais na aba Cadastros.")

    # --- 2. BUSCA AGENDAMENTOS ---
    agendamentos_dia = []
    if prof_id:
        try:
            res_ag = db.client.table('agendamentos')\
                .select('horario, id_servico, id_cliente, servicos(nome, duracao_estimada), clientes(nome)')\
                .eq('id_atendente', prof_id)\
                .eq('data_agendamento', str(dt_sel))\
                .execute()
            agendamentos_dia = res_ag.data if res_ag.data else []
        except Exception as e:
            st.error(f"Erro ao buscar agenda: {e}")

    # --- 3. VISUALIZAÇÃO GRÁFICA ---
    horarios_visuais = []
    start_time = time(8, 0) # Início do expediente
    end_time = time(19, 0)  # Fim do expediente
    
    current = datetime.combine(dt_sel, start_time)
    end_dt = datetime.combine(dt_sel, end_time)
        
    while current < end_dt:
        h_str = current.strftime('%H:%M')
        status = "Livre"
        cliente_info = "-"
        servico_info = "-"
            
        slot_start = current
        slot_end = current + timedelta(minutes=30) # Visualização em blocos de 30min
            
        for ag in agendamentos_dia:
            try:
                ag_h_str = ag['horario']
                ag_time = datetime.strptime(ag_h_str, '%H:%M:%S').time()
                ag_start = datetime.combine(dt_sel, ag_time)
                
                dur = ag['servicos']['duracao_estimada'] if ag.get('servicos') else 30
                ag_end = ag_start + timedelta(minutes=dur)
                
                # Checagem de colisão de horário
                if slot_start < ag_end and slot_end > ag_start:
                    status = "Ocupado"
                    cliente_info = ag['clientes']['nome'] if ag.get('clientes') else "?"
                    servico_info = ag['servicos']['nome'] if ag.get('servicos') else "?"
                    break
            except:
                continue
            
        horarios_visuais.append({
            "Horário": h_str,
            "Status": status,
            "Cliente": cliente_info,
            "Serviço": servico_info
        })
        current += timedelta(minutes=30)
            
    # Renderiza tabela colorida
    df_visual = pd.DataFrame(horarios_visuais)
    st.dataframe(
        df_visual.style.applymap(
            lambda v: 'background-color: #ffcdd2' if v == 'Ocupado' else 'background-color: #c8e6c9', 
            subset=['Status']
        ),
        use_container_width=True,
        height=300
    )

    st.divider()

    # --- 4. FORMULÁRIO DE NOVO AGENDAMENTO ---
    st.subheader("2. Novo Agendamento")
    
    if prof_id:
        with st.form("novo_agend"):
            c1, c2 = st.columns(2)
            
            # Select de Cliente
            if cli_dict:
                cli_id = c1.selectbox("Cliente", list(cli_dict.keys()), format_func=lambda x: cli_dict[x])
            else:
                c1.warning("Sem clientes.")
                cli_id = None
                
            # Select de Serviço
            if serv_dict:
                srv_id = c2.selectbox("Serviço", list(serv_dict.keys()), format_func=lambda x: serv_dict[x])
            else:
                c2.warning("Sem serviços.")
                srv_id = None
            
            hr_input = st.time_input("Hora de Início", time(9,0))
            
            if st.form_submit_button("✅ Confirmar Agendamento"):
                if cli_id and srv_id and prof_id:
                    try:
                        new_start = datetime.combine(dt_sel, hr_input)
                        duracao_nova = duracao_dict.get(srv_id, 30)
                        new_end = new_start + timedelta(minutes=duracao_nova)
                        
                        conflito = False
                        
                        for ag in agendamentos_dia:
                            ag_time = datetime.strptime(ag['horario'], '%H:%M:%S').time()
                            ag_start = datetime.combine(dt_sel, ag_time)
                            dur = ag['servicos']['duracao_estimada'] if ag.get('servicos') else 30
                            ag_end = ag_start + timedelta(minutes=dur)
                            
                            if new_start < ag_end and new_end > ag_start:
                                conflito = True
                                break
                        
                        if conflito:
                            st.error("❌ Conflito! Já existe um agendamento neste horário.")
                        else:
                            db.insert('agendamentos', {
                                'id_cliente': cli_id, 
                                'id_servico': srv_id, 
                                'id_atendente': prof_id,
                                'data_agendamento': str(dt_sel), 
                                'horario': str(hr_input), 
                                'status': 'Agendado'
                            })
                            st.success("Agendado com sucesso! 🎉")
                            st.session_state['refresh'] = True
                            st.rerun()
                            
                    except Exception as e:
                        st.error(f"Erro técnico: {e}")
                else:
                    st.warning("Preencha todos os campos para agendar.")
    else:
        st.info("Selecione um profissional acima para liberar o agendamento.")