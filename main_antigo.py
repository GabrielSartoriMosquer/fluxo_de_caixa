import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, time, date, timedelta
from supabase import create_client, Client

# --- CONFIGURAÇÃO INICIAL ---
st.set_page_config(
    page_title="Farmácia das Irmãs",
    page_icon="🌿",
    layout="wide"
)

# --- 1. CONEXÃO ---
@st.cache_resource
def init_connection():
    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
        return create_client(url, key)
    except Exception as e:
        st.error(f"⚠️ Erro crítico de conexão: {e}")
        return None

supabase = init_connection()

# --- 2. INICIALIZAÇÃO SEGURA DO STATE ---
tabelas_padrao = {
    'transacoes': pd.DataFrame(columns=['id', 'created_at', 'data_transacao', 'pagamento', 'origem', 'desconto', 'is_doacao', 'valor_total', 'id_cliente']),
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

# --- 3. CARREGAMENTO DE DADOS ---
def carregar_dados():
    if not supabase: return {}
    novos_dados = {}
    
    # Tabelas Simples
    for tabela in ['clientes', 'produtos', 'servicos', 'atendentes', 'transacoes', 'compras']:
        try:
            res = supabase.table(tabela).select("*").order('id', desc=True).execute()
            df = pd.DataFrame(res.data)
            if df.empty: df = tabelas_padrao[tabela]
            novos_dados[tabela] = df
        except:
            novos_dados[tabela] = tabelas_padrao[tabela]

    # Agendamentos (com Join)
    try:
        res_ag = supabase.table('agendamentos').select("*, clientes(nome), servicos(nome), atendentes(nome)").order('data_agendamento', desc=True).execute()
        dados_flat = []
        for row in res_ag.data:
            r = row.copy()
            r['Cliente'] = row['clientes']['nome'] if row.get('clientes') else 'Desconhecido'
            r['Serviço'] = row['servicos']['nome'] if row.get('servicos') else 'N/A'
            r['Profissional'] = row['atendentes']['nome'] if row.get('atendentes') else 'N/A'
            dados_flat.append(r)
        df_ag = pd.DataFrame(dados_flat)
        if df_ag.empty: df_ag = tabelas_padrao['agendamentos']
        novos_dados['agendamentos'] = df_ag
    except:
        novos_dados['agendamentos'] = tabelas_padrao['agendamentos']

    return novos_dados

# --- LÓGICA DE REFRESH ---
if 'refresh' not in st.session_state: st.session_state['refresh'] = True
if st.session_state['refresh']:
    dados_db = carregar_dados()
    if dados_db:
        for k, v in dados_db.items():
            st.session_state[k] = v
    st.session_state['refresh'] = False

# --- FUNÇÕES AUXILIARES ---
def render_generic_crud(table_name, title, fields, df_current):
    """
    Renderiza uma interface CRUD genérica para uma tabela.
    """
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
                    # Validação simples (campos required)
                    missing = [f['label'] for f in fields if f.get('required') and not payload[f['name']]]
                    if missing:
                        st.warning(f"Faltou preencher: {', '.join(missing)}")
                    else:
                        try:
                            supabase.table(table_name).insert(payload).execute()
                            st.success("Adicionado com sucesso!")
                            st.session_state['refresh'] = True
                            st.rerun()
                        except Exception as e:
                            st.error(f"Erro ao criar: {e}")

    # 3. UPDATE / DELETE (EDITAR)
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
                            val_min = f.get('min', 0.0)
                            val_init = float(current_val) if pd.notna(current_val) else val_min
                            payload_edit[f['name']] = st.number_input(f['label'], min_value=val_min, value=val_init, step=step)
                        elif f['type'] == 'textarea':
                            payload_edit[f['name']] = st.text_area(f['label'], value=str(current_val) if pd.notna(current_val) else "")
                        elif f['type'] == 'checkbox':
                            payload_edit[f['name']] = st.checkbox(f['label'], value=bool(current_val))

                    col_save, col_del = st.columns(2)
                    
                    if col_save.form_submit_button("💾 Salvar Mudanças"):
                        try:
                            supabase.table(table_name).update(payload_edit).eq('id', sel_id).execute()
                            st.success("Atualizado!")
                            st.session_state['refresh'] = True
                            st.rerun()
                        except Exception as e:
                            st.error(f"Erro ao atualizar: {e}")

                    if col_del.form_submit_button("🗑️ Apagar", type="primary"):
                        try:
                            supabase.table(table_name).delete().eq('id', sel_id).execute()
                            st.success("Apagado!")
                            st.session_state['refresh'] = True
                            st.rerun()
                        except Exception as e:
                            st.error("Não deu para apagar (pode ter vendas ou agendamentos ligados a isso).")

# --- INTERFACE ---
st.sidebar.title("Menu Principal")

menu_options = {
    "inicio": "🏠 Início",
    "vendas": "💰 Vender",
    "repor_estoque": "📦 Repor Estoque",
    "agendamento": "🗓️ Marcar Horário",
    "cadastros": "📝 Cadastros",
    "visualizacao": "🔍 Visualização"
}

page = st.sidebar.radio(
    "O que a senhora deseja fazer?", 
    list(menu_options.keys()), 
    format_func=lambda x: menu_options[x]
)


if st.sidebar.button("🔄 Atualizar Tudo"):
    st.session_state['refresh'] = True
    st.rerun()

# ---------------------------------------------------------
# PÁGINA 1: INÍCIO
# ---------------------------------------------------------
if page == "inicio":
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

# ---------------------------------------------------------
# PÁGINA 2: VENDER
# ---------------------------------------------------------
elif page == "vendas":
    st.title("💰 Fazer uma Venda")
    st.write("Preencha os dados abaixo para registrar uma venda.")
    
    with st.form("nova_venda"):
        df_c = st.session_state['clientes']
        df_p = st.session_state['produtos']
        
        # Dicionários para dropdown
        cli_opts = df_c[['id', 'nome']].set_index('id')['nome'].to_dict() if not df_c.empty else {}
        prod_opts = df_p[['id', 'nome']].set_index('id')['nome'].to_dict() if not df_p.empty else {}
        
        st.subheader("1. Detalhes da Venda")
        # [MELHORIA] Campo de Data
        c_date = st.date_input("Data da Venda", datetime.now()) 
        
        c_cli, c_prod = st.columns(2)
        if not cli_opts: st.warning("Precisa cadastrar clientes antes!"); cli_id = None
        else: cli_id = c_cli.selectbox("Cliente", list(cli_opts.keys()), format_func=lambda x: cli_opts[x])
        
        if not prod_opts: st.warning("Precisa cadastrar produtos antes!"); prod_id = None
        else: prod_id = c_prod.selectbox("Produto", list(prod_opts.keys()), format_func=lambda x: prod_opts[x])
        
        c1, c2 = st.columns(2)
        qtd = c1.number_input("Quantidade", 1, 100, 1)
        
        preco_sugerido = 0.0
        if prod_id:
            try: preco_sugerido = float(df_p.loc[df_p['id']==prod_id, 'valor_original'].values[0])
            except: pass
            
        valor = c2.number_input("Valor Total (R$)", value=float(preco_sugerido * qtd))
        
        st.subheader("2. Pagamento")
        pgto = st.selectbox("Forma de Pagamento", ["Pix", "Dinheiro", "Cartão", "Boleto"])
        
        if st.form_submit_button("✅ Finalizar Venda"):
            if cli_id and prod_id:
                try:
                    # [MELHORIA] Combina data escolhida com hora atual
                    data_final = datetime.combine(c_date, datetime.now().time())
                    
                    res_t = supabase.table('transacoes').insert({
                        'id_cliente': int(cli_id), 'valor_total': valor, 
                        'pagamento': pgto, 'origem': 'Balcão',
                        'data_transacao': str(data_final)
                    }).execute()
                    new_id = res_t.data[0]['id']
                    supabase.table('itens_transacao').insert({
                        'id_transacao': new_id, 'id_produto': int(prod_id), 
                        'quantidade': qtd, 'valor_unitario': valor
                    }).execute()
                    st.success("Venda registrada com sucesso! 🎉"); st.session_state['refresh'] = True; st.rerun()
                except Exception as e: st.error(f"Ops, deu um erro: {e}")

# ---------------------------------------------------------
# PÁGINA 3: AGENDAR
# ---------------------------------------------------------
elif page == "agendamento":
    st.title("🗓️ Marcar um Horário")
    with st.form("novo_agend"):
        cli_dict = st.session_state['clientes'].set_index('id')['nome'].to_dict() if not st.session_state['clientes'].empty else {}
        serv_dict = st.session_state['servicos'].set_index('id')['nome'].to_dict() if not st.session_state['servicos'].empty else {}
        prof_dict = st.session_state['atendentes'].set_index('id')['nome'].to_dict() if not st.session_state['atendentes'].empty else {}
        
        if cli_dict and serv_dict and prof_dict:
            st.subheader("Detalhes do Agendamento")
            cli = st.selectbox("Cliente", list(cli_dict.keys()), format_func=lambda x: cli_dict[x])
            srv = st.selectbox("Serviço", list(serv_dict.keys()), format_func=lambda x: serv_dict[x])
            prof = st.selectbox("Profissional", list(prof_dict.keys()), format_func=lambda x: prof_dict[x])
            
            c1, c2 = st.columns(2)
            dt = c1.date_input("Dia", datetime.now())
            hr = c2.time_input("Hora", time(9,0))
            
            if st.form_submit_button("✅ Agendar"):
                try:
                    supabase.table('agendamentos').insert({
                        'id_cliente': cli, 'id_servico': srv, 'id_atendente': prof,
                        'data_agendamento': str(dt), 'horario': str(hr), 'status': 'Agendado'
                    }).execute()
                    st.success("Horário marcado com sucesso! 🎉"); st.session_state['refresh'] = True; st.rerun()
                except Exception as e: st.error(f"Ops, deu um erro: {e}")
        else:
            st.warning("Faltam cadastros (Cliente, Serviço ou Profissional). Vá em 'Cadastros' primeiro.")

# ---------------------------------------------------------
# PÁGINA 4: CADASTROS
# ---------------------------------------------------------
elif page == "cadastros":
    st.title("📝 Meus Cadastros")
    st.write("Aqui a senhora pode adicionar ou mudar informações.")

    # --- CONFIGURAÇÃO DAS ABAS ---
    tab_cli, tab_prod, tab_serv, tab_eq = st.tabs(["👥 Pessoas", "📦 Produtos", "🛠️ Serviços", "👩‍⚕️ Equipe"])

    with tab_cli:
        fields_cli = [
            {'name': 'nome', 'label': 'Nome Completo', 'type': 'text', 'required': True},
            {'name': 'cpf', 'label': 'CPF', 'type': 'text'},
            {'name': 'telefone', 'label': 'Telefone', 'type': 'text'}
        ]
        render_generic_crud('clientes', 'Cliente', fields_cli, st.session_state['clientes'])

    with tab_prod:
        fields_prod = [
            {'name': 'nome', 'label': 'Nome do Produto', 'type': 'text', 'required': True},
            {'name': 'tipo', 'label': 'Tipo (ex: Chá, Óleo)', 'type': 'text'},
            {'name': 'valor_original', 'label': 'Preço (R$)', 'type': 'number', 'step': 0.01},
            {'name': 'estoque', 'label': 'Quantidade em Estoque', 'type': 'number', 'step': 1.0, 'min': 0.0}
        ]
        render_generic_crud('produtos', 'Produto', fields_prod, st.session_state['produtos'])

    with tab_serv:
        fields_serv = [
            {'name': 'nome', 'label': 'Nome do Serviço', 'type': 'text', 'required': True},
            {'name': 'valor', 'label': 'Preço (R$)', 'type': 'number', 'step': 0.01},
            {'name': 'duracao_estimada', 'label': 'Tempo (minutos)', 'type': 'number', 'step': 15.0, 'min': 15.0}
        ]
        render_generic_crud('servicos', 'Serviço', fields_serv, st.session_state['servicos'])

    with tab_eq:
        fields_eq = [
            {'name': 'nome', 'label': 'Nome da Pessoa', 'type': 'text', 'required': True},
            {'name': 'observacao', 'label': 'Anotações', 'type': 'textarea'},
            {'name': 'valor', 'label': 'Valor/Comissão (R$)', 'type': 'number', 'step': 0.01},
            {'name': 'ativo', 'label': 'Está trabalhando?', 'type': 'checkbox'}
        ]
        render_generic_crud('atendentes', 'Profissional', fields_eq, st.session_state['atendentes'])

# ---------------------------------------------------------
# PÁGINA 5: VISUALIZAÇÃO
# ---------------------------------------------------------
elif page == "visualizacao":
    st.title("🔍 Visualização Geral")
    st.write("Veja tudo o que está acontecendo na farmácia.")

    # [MELHORIA] Adicionada a aba 'Equipe'
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
            
        # Define df_t aqui dentro para usar nos gráficos
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

    # --- ABA EQUIPE (NOVO) ---
    with tab_func:
        st.subheader("👥 Nossa Equipe")
        df_func = st.session_state['atendentes']
        if not df_func.empty:
             cols_func = ['nome', 'observacao', 'valor', 'ativo']
             # Garante que só pega colunas que existem
             cols_func = [c for c in cols_func if c in df_func.columns]
             
             df_show_func = df_func[cols_func].copy()
             # Renomeia colunas para ficar bonito
             rename_map = {'nome': 'Nome', 'observacao': 'Anotações', 'valor': 'Comissão/Valor', 'ativo': 'Ativo?'}
             df_show_func = df_show_func.rename(columns=rename_map)
             
             st.dataframe(df_show_func, use_container_width=True, hide_index=True)
        else:
             st.info("Ninguém cadastrado na equipe ainda.")

    # --- ABA HORÁRIOS LIVRES ---
    with tab_livre:
        st.subheader("🆓 Consultar Horários Livres")
        dia_sel = st.date_input("Escolha o dia", datetime.now())
        
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

# ---------------------------------------------------------
# PÁGINA 6: REPOR ESTOQUE (COMPRAS)
# ---------------------------------------------------------
elif page == "repor_estoque":
    st.title("📦 Repor Estoque (Compras)")
    st.write("Registre aqui a chegada de novos produtos.")

    with st.form("nova_compra"):
        df_p = st.session_state['produtos']
        
        prod_opts = df_p[['id', 'nome']].set_index('id')['nome'].to_dict() if not df_p.empty else {}
        
        st.subheader("1. Dados da Compra")
        # [MELHORIA] Campo de Data
        c_date_compra = st.date_input("Data da Compra", datetime.now()) 
        
        if not prod_opts: st.warning("Precisa cadastrar produtos antes!"); prod_id = None
        else: prod_id = st.selectbox("Selecione o Produto", list(prod_opts.keys()), format_func=lambda x: prod_opts[x])
        
        c1, c2 = st.columns(2)
        qtd = c1.number_input("Quantidade que chegou", 1, 1000, 1)
        
        custo_unitario = 0.0
        if prod_id:
            try: custo_unitario = float(df_p.loc[df_p['id']==prod_id, 'valor_original'].values[0]) * 0.5 
            except: pass
            
        custo = c2.number_input("Custo Total da Compra (R$)", value=float(custo_unitario * qtd), step=0.01)
        
        st.subheader("2. Detalhes")
        fornecedor = st.text_input("Fornecedor (Opcional)", placeholder="Ex: Distribuidora X")
        
        if st.form_submit_button("✅ Confirmar Entrada de Estoque"):
            if prod_id:
                try:
                    # 1. Registrar a Compra
                    supabase.table('compras').insert({
                        'id_produto': int(prod_id), 
                        'quantidade': qtd, 
                        'valor_total': custo,
                        'fornecedor': fornecedor,
                        'data_compra': str(c_date_compra)
                    }).execute()
                    
                    # 2. Atualizar Estoque (+ Qtd)
                    res_p = supabase.table('produtos').select('estoque').eq('id', prod_id).execute()
                    est_atual = res_p.data[0]['estoque'] if res_p.data else 0
                    novo_estoque = est_atual + qtd
                    
                    supabase.table('produtos').update({'estoque': novo_estoque}).eq('id', prod_id).execute()
                    
                    st.success(f"Estoque atualizado! Agora temos {novo_estoque} unidades. 🎉")
                    st.session_state['refresh'] = True
                    st.rerun()
                except Exception as e: st.error(f"Ops, deu um erro: {e}")