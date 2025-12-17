import streamlit as st
from datetime import datetime
import time

def render_view():
    st.title("💰 Fazer uma Venda")
    st.write("Preencha os dados abaixo para registrar uma venda.")
    
    # Recupera o serviço de banco de dados da sessão
    db = st.session_state['db_service']
    
    # --- Seção de Recibo (Pós-Venda) ---
    if 'ultimo_recibo' in st.session_state:
        st.success("✅ Venda realizada com sucesso!")
        st.markdown("### 🧾 Comprovante de Venda")
        st.code(st.session_state['ultimo_recibo'], language="text")
        if st.button("Nova Venda"):
            del st.session_state['ultimo_recibo']
            st.rerun()
        return 
    
    # Recupera os dados atuais da sessão para preencher os selects
    df_c = st.session_state['clientes']
    df_p = st.session_state['produtos']
    
    # Dicionários para lookup
    cli_opts = {None: "👤 Consumidor Final (Sem Cadastro)"}
    if not df_c.empty:
        cli_opts.update(dict(zip(df_c['id'], df_c['nome'])))
    
    prod_opts = dict(zip(df_p['id'], df_p['nome'])) if not df_p.empty else {}
    
    # Layout de colunas
    col_data, c_cli, c_prod = st.columns([1, 2, 2])
    
    # Input de Data
    c_date = col_data.date_input("Data", datetime.now())
    
    # Seleção de Cliente
    cli_id = c_cli.selectbox("Cliente", list(cli_opts.keys()), format_func=lambda x: cli_opts[x])
    
    # Seleção de Produto
    if not prod_opts: 
        c_prod.warning("Precisa cadastrar produtos antes!")
        prod_id = None
    else: 
        prod_id = c_prod.selectbox("Produto", list(prod_opts.keys()), format_func=lambda x: prod_opts[x])
    
    # Validação de Estoque (Visualização Inicial)
    estoque_visual = 0
    pode_vender = False
    
    if prod_id and not df_p.empty:
        try:
            estoque_visual = int(df_p.loc[df_p['id']==prod_id, 'estoque'].values[0])
        except:
            estoque_visual = 0
        
        if estoque_visual > 0:
            st.info(f"📦 Estoque Atual (Cache): {estoque_visual} unidades")
            pode_vender = True
        else:
            st.error(f"🚫 Produto sem estoque! (Atual: {estoque_visual}) - Reposição necessária.")
            pode_vender = False

    c1, c2 = st.columns(2)
    
    # Limita a quantidade ao estoque disponível se houver estoque
    max_qtd = estoque_visual if estoque_visual > 0 else 1
    qtd = c1.number_input("Quantidade", 1, max_qtd, 1, disabled=not pode_vender)
    
    # Busca o preço sugerido do produto selecionado
    preco_sugerido = 0.0
    nome_produto = ""
    if prod_id and not df_p.empty:
        try: 
            val_orig = df_p.loc[df_p['id']==prod_id, 'valor_original'].values[0]
            nome_produto = df_p.loc[df_p['id']==prod_id, 'nome'].values[0]
            if val_orig is not None:
                preco_sugerido = float(val_orig)
        except: 
            pass
        
    # Checkbox de Doação
    is_donation = st.checkbox("É doação?", disabled=not pode_vender)
    
    if is_donation:
        valor = c2.number_input("Valor Total (R$)", value=0.0, disabled=True)
        st.subheader("2. Pagamento")
        pgto = st.selectbox("Forma de Pagamento", ["Doação"], disabled=True)
    else:
        valor = c2.number_input("Valor Total (R$)", value=float(preco_sugerido * qtd), disabled=not pode_vender)
        st.subheader("2. Pagamento")
        pgto = st.selectbox("Forma de Pagamento", ["Pix", "Dinheiro", "Cartão", "Boleto"], disabled=not pode_vender)
    
    st.divider()

    # Botão de Envio
    if st.button("✅ Finalizar Venda", type="primary", disabled=not pode_vender):
        if prod_id and pode_vender:
            try:
                # --- DOUBLE CHECK DE ESTOQUE ---
                res_check = db.client.table('produtos').select('estoque').eq('id', prod_id).execute()
                estoque_real = res_check.data[0]['estoque'] if res_check.data else 0
                
                if estoque_real < qtd:
                    st.error(f"⚠️ Erro de Concorrência! O estoque real é {estoque_real}, insuficiente para vender {qtd}.")
                    st.stop()
                
                data_final = datetime.combine(c_date, datetime.now().time())
                
                payload_transacao = {
                    'valor_total': valor, 
                    'pagamento': pgto, 
                    'origem': 'Balcão',
                    'data_transacao': str(data_final)
                }
                if cli_id is not None:
                    payload_transacao['id_cliente'] = int(cli_id)
                else:
                        payload_transacao['id_cliente'] = None

                # 1. Insere a transação
                res_t = db.insert('transacoes', payload_transacao)
                
                # 2. Insere itens e atualiza estoque
                if res_t.data:
                    new_id = res_t.data[0]['id']
                    
                    db.insert('itens_transacao', {
                        'id_transacao': new_id, 
                        'id_produto': int(prod_id), 
                        'quantidade': qtd, 
                        'valor_unitario': valor
                    })
                    
                    novo_estoque = estoque_real - qtd
                    db.update('produtos', {'estoque': novo_estoque}, prod_id)
                    
                    # --- GERAÇÃO DE RECIBO ---
                    nome_cliente = cli_opts.get(cli_id, "Consumidor Final")
                    recibo = f"""
                    ================================
                                FARMÁCIA 
                    ================================
                    Data: {data_final.strftime('%d/%m/%Y %H:%M')}
                    Cliente: {nome_cliente}
                    --------------------------------
                    Produto: {nome_produto}
                    Qtd: {qtd}
                    Total: R$ {valor:.2f}
                    Pagamento: {pgto}
                    --------------------------------
                    Obrigado pela preferência!
                    ================================
                    """
                    st.session_state['ultimo_recibo'] = recibo
                    st.session_state['refresh'] = True
                    st.rerun()
            except Exception as e:
                st.error(f"Erro ao registrar venda: {e}")