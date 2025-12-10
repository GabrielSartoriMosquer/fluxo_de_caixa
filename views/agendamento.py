import streamlit as st
from datetime import datetime, time, timedelta
import pandas as pd

def render_view():
    st.title("🗓️ Marcar um Horário")
    
    db = st.session_state['db_service']
    
    # Carrega dicionários para os Selectboxes
    df_cli = st.session_state['clientes']
    df_serv = st.session_state['servicos']
    df_prof = st.session_state['atendentes']
    
    cli_dict = df_cli.set_index('id')['nome'].to_dict() if not df_cli.empty else {}
    serv_dict = df_serv.set_index('id')['nome'].to_dict() if not df_serv.empty else {}
    prof_dict = df_prof.set_index('id')['nome'].to_dict() if not df_prof.empty else {}
    
    try:
        res_ag = db.client.table('agendamentos')\
            .select('horario, id_servico, id_cliente, servicos(nome, duracao_estimada), clientes(nome)')\
            .eq('id_atendente', prof_id)\
            .eq('data_agendamento', str(dt_sel))\
            .execute()
        agendamentos_dia = res_ag.data if res_ag.data else []
    except Exception as e:
        st.error(f"Erro ao buscar agenda: {e}")

    # Monta uma tabela visual de horários
    horarios_visuais = []
    # Vamos assumir horário comercial das 08:00 às 19:00 com slots de 30min para visualização
    start_time = time(8, 0)
    end_time = time(19, 0)
    current = datetime.combine(dt_sel, start_time)
    end_dt = datetime.combine(dt_sel, end_time)
        
    while current < end_dt:
        h_str = current.strftime('%H:%M')
        status = "Livre"
        cliente = "-"
        servico = "-"
            
        # Verifica se este slot colide com algum agendamento
        slot_start = current
        slot_end = current + timedelta(minutes=30) # Slot visual de 30min
            
        for ag in agendamentos_dia:
            try:
                # Converte horário do banco
                ag_h_str = ag['horario'] # pode vir "09:00:00"
                ag_time = datetime.strptime(ag_h_str, '%H:%M:%S').time()
                ag_start = datetime.combine(dt_sel, ag_time)
                    
                # Duração
                dur = ag['servicos']['duracao_estimada'] if ag.get('servicos') else 30
                ag_end = ag_start + timedelta(minutes=dur)
                    
                # Checa sobreposição: (StartA < EndB) and (EndA > StartB)
                if slot_start < ag_end and slot_end > ag_start:
                    status = "Ocupado"
                    cliente = ag['clientes']['nome'] if ag.get('clientes') else "?"
                    servico = ag['servicos']['nome'] if ag.get('servicos') else "?"
                    break
            except:
                continue
            
            horarios_visuais.append({
                "Horário": h_str,
                "Status": status,
                "Cliente": cliente,
                "Serviço": servico
            })
            current += timedelta(minutes=30)
            
        df_visual = pd.DataFrame(horarios_visuais)
        
        # Estilização condicional simples usando pandas style (se suportado) ou apenas dataframe
        st.dataframe(
            df_visual.style.applymap(
                lambda v: 'background-color: #ffcdd2' if v == 'Ocupado' else 'background-color: #c8e6c9', 
                subset=['Status']
            ),
            use_container_width=True,
            height=300
        )

        st.divider()

        st.subheader("2. Novo Agendamento")
        with st.form("novo_agend"):
            c1, c2 = st.columns(2)
            cli_id = c1.selectbox("Cliente", list(cli_dict.keys()), format_func=lambda x: cli_dict[x])
            srv_id = c2.selectbox("Serviço", list(serv_dict.keys()), format_func=lambda x: serv_dict[x])
            
            hr_input = st.time_input("Hora de Início", time(9,0))
            
            if st.form_submit_button("✅ Confirmar Agendamento"):
                # --- Lógica de Validação Robusta ---
                try:
                    # 1. Determinar intervalo do NOVO agendamento
                    new_start = datetime.combine(dt_sel, hr_input)
                    duracao_nova = duracao_dict.get(srv_id, 30) # Default 30 min se não achar
                    new_end = new_start + timedelta(minutes=duracao_nova)
                    
                    conflito = False
                    conflito_detalhe = ""
                    
                    # 2. Verificar colisão com agendamentos existentes
                    for ag in agendamentos_dia:
                        ag_h_str = ag['horario']
                        ag_time = datetime.strptime(ag_h_str, '%H:%M:%S').time()
                        ag_start = datetime.combine(dt_sel, ag_time)
                        
                        dur = ag['servicos']['duracao_estimada'] if ag.get('servicos') else 30
                        ag_end = ag_start + timedelta(minutes=dur)
                        
                        # Interseção de intervalos
                        if new_start < ag_end and new_end > ag_start:
                            conflito = True
                            conflito_detalhe = f"Conflito com {ag['servicos']['nome']} das {ag_time.strftime('%H:%M')} às {ag_end.strftime('%H:%M')}"
                            break
                    
                    if conflito:
                        st.error(f"❌ Não foi possível agendar! {conflito_detalhe}")
                    else:
                        # Inserir no banco
                        db.insert('agendamentos', {
                            'id_cliente': cli_id, 
                            'id_servico': srv_id, 
                            'id_atendente': prof_id,
                            'data_agendamento': str(dt_sel), 
                            'horario': str(hr_input), 
                            'status': 'Agendado'
                        })
                        st.success(f"Agendado com sucesso! ({hr_input.strftime('%H:%M')} - {new_end.strftime('%H:%M')}) 🎉")
                        st.session_state['refresh'] = True
                        st.rerun()
                        
                except Exception as e:
                    st.error(f"Erro técnico ao validar: {e}")

    else:
        st.warning("Faltam cadastros (Cliente, Serviço ou Profissional). Vá em 'Cadastros' primeiro.")