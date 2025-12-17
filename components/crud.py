import streamlit as st
import pandas as pd

def render_generic_crud(table_name: str, title: str, fields: list, df_current: pd.DataFrame):
    """
    Renderiza uma interface CRUD genérica para uma tabela.
    Usa o serviço de banco injetado na sessão.
    """
    db = st.session_state['db_service']
    
    st.subheader(f"Gerenciar {title}")
    
    # 1. LISTAGEM
    esconder = ['id', 'created_at']
    df_show = df_current.drop(columns=[c for c in esconder if c in df_current.columns], errors='ignore')
    st.dataframe(df_show, use_container_width=True, hide_index=True)

    c1, c2 = st.columns(2)

    # 2. CREATE (NOVO)
    with c1:
        with st.expander(f"➕ Adicionar Novo {title}", expanded=False):
            with st.form(f"form_new_{table_name}"):
                payload = {}
                for f in fields:
                    if f['type'] == 'text':
                        payload[f['name']] = st.text_input(f['label'])
                    elif f['type'] == 'number':
                        step = f.get('step', 1.0)
                        val = f.get('min', 0.0)
                        payload[f['name']] = st.number_input(f['label'], min_value=val, step=step)
                    elif f['type'] == 'textarea':
                        payload[f['name']] = st.text_area(f['label'])
                    elif f['type'] == 'checkbox':
                        payload[f['name']] = st.checkbox(f['label'], value=True)
                
                if st.form_submit_button("Salvar"):
                    missing = [f['label'] for f in fields if f.get('required') and not payload[f['name']]]
                    
                    custom_error = None
                    for f in fields:
                        if 'validator' in f and payload[f['name']]:
                            is_valid, msg = f['validator'](payload[f['name']])
                            if not is_valid:
                                custom_error = msg
                                break
                    
                    if missing:
                        st.warning(f"Faltou preencher: {', '.join(missing)}")
                    elif custom_error:
                        st.error(f"Erro de validação: {custom_error}")
                    else:
                        try:
                            clean_payload = {}
                            for k, v in payload.items():
                                field_config = next((f for f in fields if f['name'] == k), None)
                                if field_config:
                                    if k in ['estoque', 'quantidade', 'duracao_estimada']:
                                        clean_payload[k] = int(v)
                                    else:
                                        clean_payload[k] = v

                            db.insert(table_name, clean_payload)
                            st.success("Adicionado com sucesso!")
                        except Exception as e:
                            st.error(f"Erro ao criar: {e}")

    # 3. UPDATE / DELETE
    with c2:
        with st.expander(f"✏️ Alterar ou Apagar {title}", expanded=False):
            opts = df_current.set_index('id')['nome'].to_dict() if not df_current.empty else {}
            sel_id = st.selectbox(f"Escolha {title} para mudar", [None] + list(opts.keys()), format_func=lambda x: opts[x] if x else "Selecione...")

            if sel_id:
                row = df_current[df_current['id'] == sel_id].iloc[0]
                with st.form(f"form_edit_{table_name}"):
                    st.write(f"Mudando dados de: **{row['nome']}**")
                    payload_edit = {}
                    for f in fields:
                        current_val = row.get(f['name'])
                        if f['type'] == 'text':
                            payload_edit[f['name']] = st.text_input(f['label'], value=str(current_val) if pd.notna(current_val) else "")
                        elif f['type'] == 'number':
                            step = f.get('step', 1.0)
                            val_init = float(current_val) if pd.notna(current_val) else 0.0
                            payload_edit[f['name']] = st.number_input(f['label'], value=val_init, step=step)
                        elif f['type'] == 'textarea':
                            payload_edit[f['name']] = st.text_area(f['label'], value=str(current_val) if pd.notna(current_val) else "")
                        elif f['type'] == 'checkbox':
                            payload_edit[f['name']] = st.checkbox(f['label'], value=bool(current_val))

                    col_save, col_del = st.columns(2)
                    
                    if col_save.form_submit_button("💾 Salvar"):
                        try:
                            db.update(table_name, payload_edit, sel_id)
                            st.success("Atualizado!")
                            st.session_state['refresh'] = True
                            st.rerun()
                        except Exception as e:
                            st.error(f"Erro: {e}")

                    # Botão de Deletar com Confirmação
                    confirm_del = st.checkbox("⚠️ Tenho certeza que quero apagar este item")
                    if col_del.form_submit_button("🗑️ Apagar", type="primary"):
                        if confirm_del:
                            try:
                                db.delete(table_name, sel_id)
                                st.success("Apagado!")
                                st.session_state['refresh'] = True
                                st.rerun()
                            except Exception as e:
                                st.error("Erro ao apagar. Verifique se não há vendas ou agendamentos vinculados.")
                        else:
                            st.warning("Marque a caixa de confirmação acima para apagar.")