import streamlit as st
import pandas as pd
from database.crud import get_all_risks
from auth.authenticator import check_authentication
from utils.helpers import generate_pdf_report, export_to_csv

def show_reports():
    # Verifica autenticação
    if not check_authentication():
        st.error("Por favor, faça login para acessar os relatórios.")
        return

    st.title("Relatórios de Riscos")

    # Obter dados dos riscos
    risks = get_all_risks()
    if not risks:
        st.warning("Nenhum risco cadastrado.")
        return

    # Converter para DataFrame
    risk_data = [
        {
            "ID": risk.id,
            "Descrição": risk.description,
            "Probabilidade": risk.probability,
            "Impacto": risk.impact,
            "Categoria": risk.category,
            "Plano de Mitigação": risk.mitigation
        }
        for risk in risks
    ]
    df = pd.DataFrame(risk_data)

    # Resumo estatístico
    st.subheader("Resumo Estatístico")
    st.write(f"Total de Riscos: {len(df)}")
    st.write(f"Categorias Únicas: {df['Categoria'].nunique()}")
    st.write("Distribuição por Probabilidade:")
    st.write(df["Probabilidade"].value_counts())
    st.write("Distribuição por Impacto:")
    st.write(df["Impacto"].value_counts())

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
