import streamlit as st
from database.crud import create_risk, get_all_risks, update_risk, delete_risk
from database.models import Risk
from auth.authenticator import check_authentication

def show_risk_register():
    # Verifica autenticação
    if not check_authentication():
        st.error("Por favor, faça login para acessar o cadastro de riscos.")
        return

    st.title("Cadastro de Riscos")

    # Formulário para adicionar/editar risco
    st.subheader("Adicionar Novo Risco")
    with st.form(key="risk_form"):
        risk_id = st.text_input("ID do Risco (deixe em branco para novo risco)", disabled=True)
        description = st.text_area("Descrição do Risco")
        probability = st.selectbox("Probabilidade", ["Baixa", "Média", "Alta"])
        impact = st.selectbox("Impacto", ["Baixo", "Médio", "Alto"])
        category = st.text_input("Categoria")
        mitigation = st.text_area("Plano de Mitigação")
        submit_button = st.form_submit_button("Salvar Risco")

        if submit_button:
            if description and probability and impact:
                risk_data = {
                    "description": description,
                    "probability": probability,
                    "impact": impact,
                    "category": category,
                    "mitigation": mitigation
                }
                if risk_id:
                    # Atualizar risco existente
                    update_risk(risk_id, risk_data)
                    st.success("Risco atualizado com sucesso!")
                else:
                    # Criar novo risco
                    create_risk(risk_data)
                    st.success("Risco cadastrado com sucesso!")
            else:
                st.error("Por favor, preencha todos os campos obrigatórios.")

    # Exibir lista de riscos
    st.subheader("Riscos Cadastrados")
    risks = get_all_risks()
    if risks:
        for risk in risks:
            with st.expander(f"Risco: {risk.description}"):
                st.write(f"**ID**: {risk.id}")
                st.write(f"**Probabilidade**: {risk.probability}")
                st.write(f"**Impacto**: {risk.impact}")
                st.write(f"**Categoria**: {risk.category}")
                st.write(f"**Plano de Mitigação**: {risk.mitigation}")
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("Editar", key=f"edit_{risk.id}"):
                        st.session_state["edit_risk"] = risk.id
                with col2:
                    if st.button("Excluir", key=f"delete_{risk.id}"):
                        delete_risk(risk.id)
                        st.success("Risco excluído com sucesso!")
                        st.experimental_rerun()

    # Preencher formulário para edição
    if "edit_risk" in st.session_state:
        risk = next((r for r in risks if r.id == st.session_state["edit_risk"]), None)
        if risk:
            st.session_state["risk_id"] = risk.id
            st.session_state["description"] = risk.description
            st.session_state["probability"] = risk.probability
            st.session_state["impact"] = risk.impact
            st.session_state["category"] = risk.category
            st.session_state["mitigation"] = risk.mitigation
            st.experimental_rerun()

if __name__ == "__main__":
    show_risk_register()
