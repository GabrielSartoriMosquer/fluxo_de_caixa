import streamlit as st
from datetime import datetime

def render_view():
    st.title("📦 Repor Estoque (Compras)")
    st.write("Registre aqui a chegada de novos produtos.")

    db = st.session_state['db_service']
    df_p = st.session_state['produtos'] 

    with st.form("nova_compra"):
        
        c_date_compra = st.date_input("Data da Compra", datetime.now()) 
        
        prod_opts = df_p.set_index('id')['nome'].to_dict() if not df_p.empty else {}
        prod_id = None
        
        if prod_opts:
            prod_id = st.selectbox("Selecione o Produto", list(prod_opts.keys()), format_func=lambda x: prod_opts[x])
        else:
            st.warning("Nenhum produto cadastrado.")

        c1, c2 = st.columns(2)
        qtd = c1.number_input("Quantidade que chegou", 1, 1000, 1)
            
        custo_unitario = 0.0
        if prod_id and not df_p.empty:
            try: 
                val_orig = df_p.loc[df_p['id']==prod_id, 'valor_original'].values[0]
                if val_orig is not None:
                    custo_unitario = float(val_orig) * 0.5 
            except: 
                pass
                
        custo = c2.number_input("Custo Total da Compra (R$)", value=float(custo_unitario * qtd), step=0.01)
            
        st.subheader("2. Detalhes")
        fornecedor = st.text_input("Fornecedor (Opcional)", placeholder="Ex: Distribuidora X")
            
        if st.form_submit_button("✅ Confirmar Entrada de Estoque"):
            if prod_id:
                try:
                    # 1. Registrar a Compra
                    db.insert('compras', {
                        'id_produto': int(prod_id), 
                        'quantidade': int(qtd), 
                        'valor_total': custo,
                        'fornecedor': fornecedor,
                        'data_compra': str(c_date_compra)
                    })
                        
                    # 2. Atualizar Estoque 
                    res_p = db.client.table('produtos').select('estoque').eq('id', prod_id).execute()
                    est_atual = res_p.data[0]['estoque'] if res_p.data else 0
                    novo_estoque = int(est_atual) + int(qtd)
                        
                    db.update('produtos', {'estoque': novo_estoque}, prod_id)
                        
                    st.success(f"Estoque atualizado! Agora temos {novo_estoque} unidades. 🎉")
                    st.session_state['refresh'] = True
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao repor estoque: {e}")