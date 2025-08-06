import streamlit as st
import pandas as pd
from database.crud import get_all_risks
from utils.charts import create_risk_matrix, create_category_bar_chart
from auth.authenticator import check_authentication

def show_dashboard():
    # Verifica autenticação
    if not check_authentication():
        st.error("Por favor, faça login para acessar o dashboard.")
        return

    st.title("Dashboard de Gerenciamento de Riscos")

    # Obter dados dos riscos
    risks = get_all_risks()
    if not risks:
        st.warning("Nenhum risco cadastrado.")
        return

    # Converter para DataFrame para facilitar manipulação
    risk_data = [
        {
            "Descrição": risk.description,
            "Probabilidade": risk.probability,
            "Impacto": risk.impact,
            "Categoria": risk.category
        }
        for risk in risks
    ]
    df = pd.DataFrame(risk_data)

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
