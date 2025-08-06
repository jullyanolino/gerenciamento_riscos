import streamlit as st
from auth.authenticator import check_authentication

# Configuração inicial do Streamlit
st.set_page_config(
    page_title="Gerenciamento de Riscos",
    page_icon="⚠️",
    layout="wide",
    initial_sidebar_state="expanded"
)

def main():
    # Verificar autenticação
    if check_authentication():
        # Barra lateral para navegação
        st.sidebar.title("Gerenciamento de Riscos")
        st.sidebar.markdown("Navegue pelas funcionalidades abaixo:")
        
        # As páginas são automaticamente carregadas do diretório pages/
        # A barra lateral pode incluir links ou informações adicionais
        st.sidebar.info("Use o menu para acessar o Cadastro de Riscos, Dashboard ou Relatórios.")
        
        # Mensagem de boas-vindas na página principal
        st.title("Sistema de Gerenciamento de Riscos")
        st.markdown("""
        Este sistema permite gerenciar riscos de forma eficiente. Utilize as opções na barra lateral para:
        - **Cadastrar e gerenciar riscos** no Cadastro de Riscos.
        - **Visualizar gráficos e análises** no Dashboard.
        - **Gerar relatórios detalhados** em Relatórios.
        """)
    else:
        # Exibir mensagem de login se não autenticado
        st.error("Por favor, faça login para acessar o sistema.")
        st.markdown("Entre com suas credenciais na página de login.")

if __name__ == "__main__":
    main()
