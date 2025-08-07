import streamlit as st
import pandas as pd
from auth.azure_ad import HybridAuthenticator, create_environment_config
from database.connection import session_scope
from database.crud import RiscoCRUD, RelatoriosCRUD
from utils.helpers import generate_pdf_report, export_to_csv

def show_reports():
    # Configurar autenticação
    config = create_environment_config()
    auth = HybridAuthenticator(local_config=config['local'], azure_config=config['azure'])
    
    if not auth.require_authentication():
        st.stop()
    
    st.title("Relatórios de Riscos")
    
    # Obter dados dos riscos
    with session_scope() as session:
        df = RelatoriosCRUD.relatorio_matriz_riscos(session)
        if df.empty:
            st.warning("Nenhum risco cadastrado.")
            return
        
        # Resumo estatístico
        st.subheader("Resumo Estatístico")
        st.write(f"Total de Riscos: {len(df)}")
        st.write(f"Categorias Únicas: {df['categoria'].nunique()}")
        st.write("Distribuição por Probabilidade:")
        st.write(df["probabilidade"].value_counts())
        st.write("Distribuição por Impacto:")
        st.write(df["impacto"].value_counts())
        st.write("Distribuição por Criticidade:")
        st.write(df["criticidade"].value_counts())
        
        # Exibir tabela completa
        st.subheader("Tabela de Riscos")
        st.dataframe(df)
        
        # Exportação de relatórios
        st.subheader("Exportar Relatório")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Gerar Relatório em PDF"):
                pdf_file = generate_pdf_report(df)
                st.download_button(
                    label="Baixar PDF",
                    data=pdf_file,
                    file_name="relatorio_riscos.pdf",
                    mime="application/pdf"
                )
        with col2:
            if st.button("Exportar para CSV"):
                csv_file = export_to_csv(df)
                st.download_button(
                    label="Baixar CSV",
                    data=csv_file,
                    file_name="relatorio_riscos.csv",
                    mime="text/csv"
                )

if __name__ == "__main__":
    show_reports()
