import streamlit as st
from auth.azure_ad import HybridAuthenticator, create_environment_config
from database.connection import session_scope
from database.crud import RiscoCRUD
from database.models import NivelProbabilidade, NivelImpacto, CategoriaRisco, FonteRisco, TipoResposta

def show_risk_register():
    # Configurar autenticação
    config = create_environment_config()
    auth = HybridAuthenticator(local_config=config['local'], azure_config=config['azure'])
    
    if not auth.require_authentication():
        st.stop()
    
    st.title("Cadastro de Riscos")
    
    # Obter ID do usuário autenticado
    user_info = auth.get_user_info()
    usuario_id = 1  # Substituir por ID real do usuário do banco, se disponível
    
    # Formulário para adicionar/editar risco
    st.subheader("Adicionar/Editar Risco")
    edit_risk_id = st.session_state.get("edit_risk_id", None)
    
    with st.form(key="risk_form"):
        if edit_risk_id:
            with session_scope() as session:
                risco = session.query(Risco).filter_by(id=edit_risk_id).first()
                default_values = {
                    "eap": risco.eap,
                    "fonte": risco.fonte,
                    "categoria": risco.categoria,
                    "titulo_evento": risco.titulo_evento,
                    "descricao_evento": risco.descricao_evento,
                    "causas": risco.causas,
                    "tipo_impacto": risco.tipo_impacto,
                    "consequencias": risco.consequencias,
                    "probabilidade": risco.probabilidade,
                    "impacto": risco.impacto,
                    "resposta_adotada": risco.resposta_adotada
                }
        else:
            default_values = {}
        
        eap = st.text_input("EAP", value=default_values.get("eap", ""))
        fonte = st.selectbox("Fonte", [f.value for f in FonteRisco], 
                            index=[f.value for f in FonteRisco].index(default_values.get("fonte", "Operacional")) if default_values.get("fonte") else 0)
        categoria = st.selectbox("Categoria", [c.value for c in CategoriaRisco], 
                                index=[c.value for c in CategoriaRisco].index(default_values.get("categoria", "Conformidade")) if default_values.get("categoria") else 0)
        titulo_evento = st.text_input("Título do Evento", value=default_values.get("titulo_evento", ""))
        descricao_evento = st.text_area("Descrição do Evento", value=default_values.get("descricao_evento", ""))
        causas = st.text_area("Causas", value=default_values.get("causas", ""))
        tipo_impacto = st.selectbox("Tipo de Impacto", [t.value for t in TipoImpacto], 
                                   index=[t.value for t in TipoImpacto].index(default_values.get("tipo_impacto", "Objetivo do projeto")) if default_values.get("tipo_impacto") else 0)
        consequencias = st.text_area("Consequências", value=default_values.get("consequencias", ""))
        probabilidade = st.selectbox("Probabilidade", [p.value for p in NivelProbabilidade], 
                                    index=[p.value for p in NivelProbabilidade].index(default_values.get("probabilidade", "Média")) if default_values.get("probabilidade") else 0)
        impacto = st.selectbox("Impacto", [i.value for i in NivelImpacto], 
                              index=[i.value for i in NivelImpacto].index(default_values.get("impacto", "Moderado")) if default_values.get("impacto") else 0)
        resposta_adotada = st.selectbox("Resposta Adotada", [r.value for r in TipoResposta], 
                                       index=[r.value for r in TipoResposta].index(default_values.get("resposta_adotada", "Mitigar")) if default_values.get("resposta_adotada") else 0)
        
        submit_button = st.form_submit_button("Salvar Risco")
        
        if submit_button:
            if all([eap, titulo_evento, descricao_evento, causas, consequencias]):
                risco_data = {
                    "eap": eap,
                    "fonte": fonte,
                    "categoria": categoria,
                    "titulo_evento": titulo_evento,
                    "descricao_evento": descricao_evento,
                    "causas": causas,
                    "tipo_impacto": tipo_impacto,
                    "consequencias": consequencias,
                    "probabilidade": probabilidade,
                    "impacto": impacto,
                    "resposta_adotada": resposta_adotada
                }
                with session_scope() as session:
                    if edit_risk_id:
                        RiscoCRUD.atualizar_risco(session, edit_risk_id, risco_data)
                        st.success("Risco atualizado com sucesso!")
                        del st.session_state["edit_risk_id"]
                    else:
                        RiscoCRUD.criar_risco(session, risco_data, usuario_id)
                        st.success("Risco cadastrado com sucesso!")
                    st.rerun()
            else:
                st.error("Por favor, preencha todos os campos obrigatórios.")
    
    # Botão para limpar formulário de edição
    if edit_risk_id and st.button("Cancelar Edição"):
        del st.session_state["edit_risk_id"]
        st.rerun()
    
    # Exibir lista de riscos
    st.subheader("Riscos Cadastrados")
    with session_scope() as session:
        riscos, total = RiscoCRUD.listar_riscos(session, filtros={'ativo': True})
        if riscos:
            df = pd.DataFrame([{
                'id': r.id,
                'titulo_evento': r.titulo_evento,
                'probabilidade': r.probabilidade,
                'impacto': r.impacto,
                'categoria': r.categoria,
                'resposta_adotada': r.resposta_adotada,
                'criticidade': r.criticidade
            } for r in riscos])
            for risco in riscos:
                with st.expander(f"Risco: {risco.titulo_evento}"):
                    st.write(f"**ID**: {risco.id}")
                    st.write(f"**EAP**: {risco.eap}")
                    st.write(f"**Fonte**: {risco.fonte}")
                    st.write(f"**Categoria**: {risco.categoria}")
                    st.write(f"**Descrição**: {risco.descricao_evento}")
                    st.write(f"**Causas**: {risco.causas}")
                    st.write(f"**Tipo de Impacto**: {risco.tipo_impacto}")
                    st.write(f"**Consequências**: {risco.consequencias}")
                    st.write(f"**Probabilidade**: {risco.probabilidade}")
                    st.write(f"**Impacto**: {risco.impacto}")
                    st.write(f"**Criticidade**: {risco.criticidade}")
                    st.write(f"**Resposta Adotada**: {risco.resposta_adotada}")
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("Editar", key=f"edit_{risco.id}"):
                            st.session_state["edit_risk_id"] = risco.id
                            st.rerun()
                    with col2:
                        if st.button("Excluir", key=f"delete_{risco.id}"):
                            RiscoCRUD.deletar_risco(session, risco.id)
                            st.success("Risco excluído com sucesso!")
                            st.rerun()
        else:
            st.warning("Nenhum risco cadastrado.")

if __name__ == "__main__":
    show_risk_register()
