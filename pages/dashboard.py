import streamlit as st
import pandas as pd
from auth.azure_ad import HybridAuthenticator, create_environment_config
from database.connection import session_scope
from database.crud import RelatoriosCRUD
from utils.charts import create_risk_matrix, create_category_bar_chart

def show_dashboard():
    # Configurar autenticação
    config = create_environment_config()
    auth = HybridAuthenticator(local_config=config['local'], azure_config=config['azure'])
    
    if not auth.require_authentication():
        st.stop()
    
    st.title("Dashboard de Gerenciamento de Riscos")
    
    # Obter dados dos riscos
    with session_scope() as session:
        df = RelatoriosCRUD.relatorio_matriz_riscos(session)
        if df.empty:
            st.warning("Nenhum risco cadastrado.")
            return
        
        # Matriz de Riscos
        st.subheader("Matriz de Riscos")
        fig = create_risk_matrix(df)
        st.plotly_chart(fig, use_container_width=True)
        
        # Gráfico de barras por categoria
        st.subheader("Distribuição de Riscos por Categoria")
        fig = create_category_bar_chart(df)
        st.plotly_chart(fig, use_container_width=True)
        
        # Tabela de riscos
        st.subheader("Tabela de Riscos")
        st.dataframe(df)

if __name__ == "__main__":
    show_dashboard()
