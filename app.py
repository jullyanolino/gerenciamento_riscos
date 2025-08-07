import streamlit as st
from auth.azure_ad import HybridAuthenticator, create_environment_config
from database.connection import init_database, get_session
from database.models import Usuario
from database.crud import UsuarioCRUD
from datetime import datetime

# Inicializar banco de dados
init_database()

# Configuração inicial do Streamlit
st.set_page_config(
    page_title="Gerenciamento de Riscos",
    page_icon="⚠️",
    layout="wide",
    initial_sidebar_state="expanded"
)

def sync_user_with_db(user_info, session):
    """
    Sincroniza informações do usuário autenticado com a tabela usuarios.
    Argumentos:
        user_info (dict): Informações do usuário do Azure AD ou autenticação local.
        session (Session): Sessão do banco de dados.
    """
    if not user_info:
        return
    
    username = user_info.get('username')
    email = user_info.get('email')
    name = user_info.get('name')
    role = user_info.get('role', 'user')
    
    # Verificar se usuário existe no banco
    usuario = session.query(Usuario).filter_by(username=username).first()
    if not usuario:
        usuario_data = {
            'username': username,
            'email': email,
            'nome_completo': name,
            'role': role,
            'criado_em': datetime.now(),
            'criado_por_id': 1  # Admin padrão
        }
        usuario = UsuarioCRUD.criar_usuario(session, usuario_data)
    else:
        # Atualizar informações, se necessário
        usuario.email = email
        usuario.nome_completo = name
        usuario.role = role
        usuario.atualizado_em = datetime.now()
    
    session.commit()

def main():
    # Carregar configurações de autenticação
    config = create_environment_config()
    
    # Configuração de fallback para desenvolvimento
    if not config['azure']:
        from auth.authenticator import create_sample_config
        config['local'] = create_sample_config()
    
    # Inicializar autenticador híbrido
    auth = HybridAuthenticator(
        local_config=config['local'],
        azure_config=config['azure']
    )
    
    # Verificar autenticação
    name, username, auth_status = auth.check_authentication()
    
    if auth_status:
        # Sincronizar usuário com banco
        with get_session() as session:
            sync_user_with_db(auth.get_user_info(), session)
        
        # Usuário autenticado
        user_info = auth.get_user_info()
        
        # Configurar barra lateral
        with st.sidebar:
            st.success(f"✅ Bem-vindo(a), {user_info.get('name', 'Usuário')}")
            st.info(f"📧 {user_info.get('email', 'N/A')}")
            st.info(f"🎭 {st.session_state.get('user_role', 'user')}")
            auth.logout(location='sidebar')
            
            st.markdown("---")
            st.markdown("### Navegação")
            st.info("Use o menu do Streamlit para acessar o Cadastro de Riscos, Dashboard ou Relatórios.")
        
        # Conteúdo principal
        st.title("Sistema de Gerenciamento de Riscos")
        st.markdown("""
        Bem-vindo ao sistema de gerenciamento de riscos. Utilize as opções na barra lateral para:
        - **Cadastrar e gerenciar riscos** no Cadastro de Riscos.
        - **Visualizar gráficos e análises** no Dashboard.
        - **Gerar relatórios detalhados** em Relatórios.
        """)
        
        # Exemplo de controle de acesso por função
        if auth.require_role(['admin', 'manager']):
            st.header("🔧 Área Administrativa")
            st.write("Conteúdo exclusivo para administradores e gerentes.")
    else:
        # Usuário não autenticado - exibir tela de login
        st.title("🔐 Login - Gerenciamento de Riscos")
        st.markdown("Faça login para acessar o sistema.")
        
        # Tentar autenticação com fallback
        try:
            auth_method = 'azure' if config['azure'] else 'local'
            if not config['azure'] and not config['local']:
                st.error("❌ Nenhuma configuração de autenticação encontrada. Contate o administrador.")
                st.stop()
                
            name, username, auth_status = auth.login(auth_method=auth_method, location='main')
            if auth_status:
                st.rerun()
                
        except Exception as e:
            st.error(f"❌ Erro na autenticação Azure AD: {str(e)}")
            st.warning("Tentando autenticação local como fallback...")
            name, username, auth_status = auth.login(auth_method='local', location='main')
            if auth_status:
                st.rerun()

if __name__ == "__main__":
    main()
