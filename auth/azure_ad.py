# auth/azure_ad.py

import streamlit as st
import msal
import requests
from typing import Optional, Dict, List, Tuple
import json
import os
from datetime import datetime, timedelta
import base64
import hashlib

class AzureADAuthenticator:
    """
    Integração com Azure Active Directory para autenticação
    Suporta MFA e Single Sign-On
    """
    
    def __init__(self, config: Dict):
        """
        Inicializa autenticador Azure AD
        
        Args:
            config: Configurações do Azure AD contendo:
                - client_id: ID da aplicação registrada no Azure
                - client_secret: Secret da aplicação (opcional para public clients)
                - authority: URL da autoridade (tenant)
                - redirect_uri: URI de redirecionamento
                - scopes: Lista de escopos necessários
        """
        self.client_id = config['client_id']
        self.client_secret = config.get('client_secret')
        self.authority = config.get('authority', f"https://login.microsoftonline.com/{config.get('tenant_id', 'common')}")
        self.redirect_uri = config['redirect_uri']
        self.scopes = config.get('scopes', ['User.Read'])
        
        # Configuração MSAL
        if self.client_secret:
            # Confidential client (com secret)
            self.app = msal.ConfidentialClientApplication(
                client_id=self.client_id,
                client_credential=self.client_secret,
                authority=self.authority
            )
        else:
            # Public client (sem secret)
            self.app = msal.PublicClientApplication(
                client_id=self.client_id,
                authority=self.authority
            )
            
    def get_auth_url(self) -> str:
        """
        Gera URL de autorização para login
        
        Returns:
            URL para redirecionamento ao Azure AD
        """
        # Gera state para segurança CSRF
        state = base64.urlsafe_b64encode(os.urandom(32)).decode('utf-8')
        st.session_state['auth_state'] = state
        
        auth_url = self.app.get_authorization_request_url(
            scopes=self.scopes,
            redirect_uri=self.redirect_uri,
            state=state
        )
        return auth_url
        
    def handle_auth_callback(self, auth_response: Dict) -> Optional[Dict]:
        """
        Processa callback de autenticação do Azure AD
        
        Args:
            auth_response: Resposta de autorização contendo code e state
            
        Returns:
            Dicionário com informações do usuário ou None se falhar
        """
        # Verifica state para prevenir CSRF
        if auth_response.get('state') != st.session_state.get('auth_state'):
            st.error("🚫 Erro de segurança: State inválido")
            return None
            
        if 'error' in auth_response:
            st.error(f"❌ Erro na autenticação: {auth_response.get('error_description', 'Erro desconhecido')}")
            return None
            
        if 'code' not in auth_response:
            st.error("❌ Código de autorização não recebido")
            return None
            
        try:
            # Troca o código por token
            result = self.app.acquire_token_by_authorization_code(
                auth_response['code'],
                scopes=self.scopes,
                redirect_uri=self.redirect_uri
            )
            
            if 'access_token' in result:
                # Salva tokens na sessão
                st.session_state['azure_access_token'] = result['access_token']
                st.session_state['azure_refresh_token'] = result.get('refresh_token')
                st.session_state['azure_token_expires'] = datetime.now() + timedelta(seconds=result.get('expires_in', 3600))
                
                # Obtém informações do usuário
                user_info = self.get_user_info(result['access_token'])
                if user_info:
                    self._set_user_session(user_info)
                    return user_info
                    
            else:
                error_msg = result.get('error_description', 'Falha na obtenção do token')
                st.error(f"❌ Erro ao obter token: {error_msg}")
                return None
                
        except Exception as e:
            st.error(f"❌ Erro durante autenticação: {str(e)}")
            return None
            
    def get_user_info(self, access_token: str) -> Optional[Dict]:
        """
        Obtém informações do usuário usando Microsoft Graph API
        
        Args:
            access_token: Token de acesso do Azure AD
            
        Returns:
            Dicionário com informações do usuário
        """
        try:
            headers = {'Authorization': f'Bearer {access_token}'}
            
            # Chama Microsoft Graph para obter perfil do usuário
            response = requests.get(
                'https://graph.microsoft.com/v1.0/me',
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                user_data = response.json()
                
                # Estrutura padronizada de retorno
                return {
                    'id': user_data.get('id'),
                    'username': user_data.get('userPrincipalName', '').lower(),
                    'email': user_data.get('mail') or user_data.get('userPrincipalName'),
                    'name': user_data.get('displayName'),
                    'first_name': user_data.get('givenName'),
                    'last_name': user_data.get('surname'),
                    'job_title': user_data.get('jobTitle'),
                    'department': user_data.get('department'),
                    'office_location': user_data.get('officeLocation'),
                    'phone': user_data.get('mobilePhone') or user_data.get('businessPhones', [None])[0],
                    'auth_method': 'azure_ad'
                }
            else:
                st.error(f"❌ Erro ao obter dados do usuário: {response.status_code}")
                return None
                
        except Exception as e:
            st.error(f"❌ Erro na consulta ao Graph API: {str(e)}")
            return None
            
    def _set_user_session(self, user_info: Dict):
        """Define informações do usuário na sessão"""
        st.session_state['authentication_status'] = True
        st.session_state['name'] = user_info['name']
        st.session_state['username'] = user_info['username']
        st.session_state['email'] = user_info['email']
        st.session_state['user_role'] = self._determine_user_role(user_info)
        st.session_state['azure_user_info'] = user_info
        
    def _determine_user_role(self, user_info: Dict) -> str:
        """
        Determina função do usuário baseado em regras de negócio
        Pode ser customizado conforme necessidades da organização
        
        Args:
            user_info: Informações do usuário do Azure AD
            
        Returns:
            String com a função ('admin', 'manager', 'user', 'viewer')
        """
        email = user_info.get('email', '').lower()
        department = user_info.get('department', '').lower()
        job_title = user_info.get('job_title', '').lower()
        
        # Regras de negócio para determinação de função
        # Administradores (customize conforme sua organização)
        admin_emails = [
            'admin@suaempresa.com',
            'it@suaempresa.com',
            'ti@suaempresa.com'
        ]
        
        admin_keywords = ['admin', 'administrador', 'ti', 'it', 'diretor']
        manager_keywords = ['gerente', 'manager', 'coordenador', 'supervisor', 'líder']
        
        if email in admin_emails:
            return 'admin'
            
        if any(keyword in job_title for keyword in admin_keywords):
            return 'admin'
            
        if any(keyword in job_title for keyword in manager_keywords):
            return 'manager'
            
        if 'risco' in department or 'compliance' in department:
            return 'user'
            
        # Função padrão
        return 'viewer'
        
    def check_authentication(self) -> Tuple[Optional[str], Optional[str], Optional[bool]]:
        """
        Verifica se usuário está autenticado via Azure AD
        
        Returns:
            Tuple com (nome, username, authentication_status)
        """
        # Verifica se há sessão ativa
        if st.session_state.get('authentication_status') and st.session_state.get('azure_access_token'):
            # Verifica se token ainda é válido
            token_expires = st.session_state.get('azure_token_expires')
            if token_expires and datetime.now() < token_expires:
                return (
                    st.session_state.get('name'),
                    st.session_state.get('username'),
                    True
                )
            else:
                # Token expirado, tenta renovar
                if self.refresh_token():
                    return (
                        st.session_state.get('name'),
                        st.session_state.get('username'),
                        True
                    )
                else:
                    self.logout()
                    
        return None, None, None
        
    def refresh_token(self) -> bool:
        """
        Renova token de acesso usando refresh token
        
        Returns:
            True se conseguiu renovar, False caso contrário
        """
        refresh_token = st.session_state.get('azure_refresh_token')
        if not refresh_token:
            return False
            
        try:
            result = self.app.acquire_token_by_refresh_token(
                refresh_token,
                scopes=self.scopes
            )
            
            if 'access_token' in result:
                st.session_state['azure_access_token'] = result['access_token']
                st.session_state['azure_refresh_token'] = result.get('refresh_token', refresh_token)
                st.session_state['azure_token_expires'] = datetime.now() + timedelta(seconds=result.get('expires_in', 3600))
                return True
            else:
                return False
                
        except Exception:
            return False
            
    def login_button(self, button_text: str = "🔐 Entrar com Microsoft", location: str = 'main') -> bool:
        """
        Renderiza botão de login com Azure AD
        
        Args:
            button_text: Texto do botão
            location: Onde renderizar ('main', 'sidebar')
            
        Returns:
            True se login foi iniciado
        """
        # Verifica se já está autenticado
        name, username, auth_status = self.check_authentication()
        if auth_status:
            return True
            
        if location == 'sidebar':
            container = st.sidebar
        else:
            container = st
            
        with container:
            st.markdown("### 🏢 Login Corporativo")
            
            if st.button(button_text, key="azure_login_btn"):
                auth_url = self.get_auth_url()
                st.markdown(f"""
                <script>
                    window.open('{auth_url}', '_blank');
                </script>
                """, unsafe_allow_html=True)
                
                st.info("🔄 Você será redirecionado para o login da Microsoft. Após autenticar, cole a URL de retorno abaixo:")
                
                # Campo para colar URL de retorno (workaround para Streamlit)
                callback_url = st.text_input(
                    "Cole aqui a URL completa após o login:",
                    placeholder="https://seuapp.com/?code=...",
                    key="azure_callback_url"
                )
                
                if callback_url and 'code=' in callback_url:
                    # Parse da URL de callback
                    auth_response = self._parse_callback_url(callback_url)
                    if auth_response:
                        user_info = self.handle_auth_callback(auth_response)
                        if user_info:
                            st.success(f"✅ Login realizado com sucesso! Bem-vindo(a), {user_info['name']}")
                            st.rerun()
                            return True
                        
        return False
        
    def _parse_callback_url(self, url: str) -> Optional[Dict]:
        """
        Extrai parâmetros da URL de callback
        
        Args:
            url: URL de callback completa
            
        Returns:
            Dicionário com parâmetros extraídos
        """
        try:
            from urllib.parse import urlparse, parse_qs
            
            parsed = urlparse(url)
            params = parse_qs(parsed.query)
            
            # Converte listas em valores únicos
            result = {}
            for key, value_list in params.items():
                result[key] = value_list[0] if value_list else None
                
            return result
            
        except Exception:
            return None
            
    def logout(self, clear_browser_cache: bool = True):
        """
        Realiza logout do Azure AD
        
        Args:
            clear_browser_cache: Se deve limpar cache do navegador
        """
        # Limpa sessão Streamlit
        azure_keys = [
            'authentication_status', 'name', 'username', 'email', 'user_role',
            'azure_access_token', 'azure_refresh_token', 'azure_token_expires',
            'azure_user_info', 'auth_state'
        ]
        
        for key in azure_keys:
            if key in st.session_state:
                del st.session_state[key]
                
        if clear_browser_cache:
            # URL para logout do Azure AD (limpa sessão no navegador)
            logout_url = f"{self.authority}/oauth2/v2.0/logout?post_logout_redirect_uri={self.redirect_uri}"
            st.markdown(f"""
            <script>
                window.location.href = '{logout_url}';
            </script>
            """, unsafe_allow_html=True)
            
        st.success("✅ Logout realizado com sucesso!")
        
    def get_user_groups(self) -> List[str]:
        """
        Obtém grupos do usuário no Azure AD
        
        Returns:
            Lista de grupos que o usuário pertence
        """
        access_token = st.session_state.get('azure_access_token')
        if not access_token:
            return []
            
        try:
            headers = {'Authorization': f'Bearer {access_token}'}
            response = requests.get(
                'https://graph.microsoft.com/v1.0/me/memberOf',
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                groups_data = response.json()
                groups = []
                
                for group in groups_data.get('value', []):
                    if group.get('@odata.type') == '#microsoft.graph.group':
                        groups.append(group.get('displayName'))
                        
                return groups
            else:
                return []
                
        except Exception:
            return []
            
    def check_group_membership(self, required_groups: List[str]) -> bool:
        """
        Verifica se usuário pertence a algum dos grupos especificados
        
        Args:
            required_groups: Lista de grupos necessários
            
        Returns:
            True se pertence a pelo menos um grupo
        """
        user_groups = self.get_user_groups()
        return any(group in user_groups for group in required_groups)

def create_azure_config_sample() -> Dict:
    """Cria configuração de exemplo para Azure AD"""
    return {
        'client_id': 'SEU_CLIENT_ID_AQUI',
        'client_secret': 'SEU_CLIENT_SECRET_AQUI',  # Opcional para public clients
        'tenant_id': 'SEU_TENANT_ID_OU_COMMON',
        'redirect_uri': 'https://seuapp.streamlit.app',  # URL do seu app
        'scopes': ['User.Read', 'Group.Read.All'],  # Permissões necessárias
        'authority': None  # Será gerado automaticamente
    }

# Função utilitária para configuração rápida
def setup_azure_ad(client_id: str, tenant_id: str = 'common', 
                  redirect_uri: str = None, client_secret: str = None) -> AzureADAuthenticator:
    """
    Configuração rápida do Azure AD
    
    Args:
        client_id: ID da aplicação no Azure
        tenant_id: ID do tenant (ou 'common' para multi-tenant)
        redirect_uri: URI de redirecionamento
        client_secret: Secret da aplicação (opcional)
        
    Returns:
        Instância configurada do AzureADAuthenticator
    """
    if not redirect_uri:
        # Tenta detectar URL atual do Streamlit
        try:
            import streamlit.web.server.server as streamlit_server
            redirect_uri = f"http://localhost:8501"
        except:
            redirect_uri = "http://localhost:8501"
    
    config = {
        'client_id': client_id,
        'tenant_id': tenant_id,
        'redirect_uri': redirect_uri,
        'scopes': ['User.Read', 'Group.Read.All']
    }
    
    if client_secret:
        config['client_secret'] = client_secret
        
    return AzureADAuthenticator(config)

class HybridAuthenticator:
    """
    Autenticador híbrido que combina autenticação local e Azure AD
    Permite fallback entre os métodos de autenticação
    """
    
    def __init__(self, local_config: Dict = None, azure_config: Dict = None):
        """
        Inicializa autenticador híbrido
        
        Args:
            local_config: Configuração para autenticação local
            azure_config: Configuração para Azure AD
        """
        self.local_auth = None
        self.azure_auth = None
        
        if local_config:
            from .authenticator import StreamlitAuthenticator
            self.local_auth = StreamlitAuthenticator(local_config)
            
        if azure_config:
            self.azure_auth = AzureADAuthenticator(azure_config)
            
    def login(self, auth_method: str = 'both', location: str = 'main'):
        """
        Renderiza opções de login
        
        Args:
            auth_method: 'local', 'azure', ou 'both'
            location: Onde renderizar ('main', 'sidebar')
        """
        # Verifica autenticação existente
        name, username, auth_status = self.check_authentication()
        if auth_status:
            return name, username, auth_status
            
        if location == 'sidebar':
            container = st.sidebar
        else:
            container = st
            
        with container:
            st.markdown("### 🔐 Sistema de Autenticação")
            
            if auth_method in ['both', 'azure'] and self.azure_auth:
                st.markdown("#### Acesso Corporativo")
                if self.azure_auth.login_button("🏢 Entrar com Microsoft", location='current'):
                    return self.check_authentication()
                    
                if auth_method == 'both':
                    st.markdown("---")
                    
            if auth_method in ['both', 'local'] and self.local_auth:
                st.markdown("#### Acesso Local")
                name, username, auth_status = self.local_auth.login(location='current')
                if auth_status is not None:
                    return name, username, auth_status
                    
        return None, None, None
        
    def check_authentication(self):
        """Verifica autenticação em ambos os métodos"""
        # Prioriza Azure AD se disponível
        if self.azure_auth:
            name, username, auth_status = self.azure_auth.check_authentication()
            if auth_status:
                return name, username, auth_status
                
        # Fallback para autenticação local
        if self.local_auth:
            return self.local_auth.check_authentication()
            
        return None, None, None
        
    def logout(self, location: str = 'sidebar'):
        """Realiza logout de ambos os sistemas"""
        if location == 'sidebar':
            if st.sidebar.button("🚪 Logout"):
                self._perform_logout()
        else:
            if st.button("🚪 Logout"):
                self._perform_logout()
                
    def _perform_logout(self):
        """Executa logout em ambos os sistemas"""
        if self.azure_auth:
            self.azure_auth.logout(clear_browser_cache=False)
            
        if self.local_auth:
            self.local_auth._perform_logout()
            
        st.rerun()
        
    def get_user_info(self) -> Optional[Dict]:
        """Retorna informações do usuário logado"""
        # Prioriza informações do Azure AD
        if st.session_state.get('azure_user_info'):
            return st.session_state['azure_user_info']
            
        # Fallback para autenticação local
        if self.local_auth:
            return self.local_auth.get_user_info()
            
        return None
        
    def require_authentication(self, auth_method: str = 'both') -> bool:
        """
        Exige autenticação para acessar conteúdo
        
        Args:
            auth_method: Método de autenticação aceito ('local', 'azure', 'both')
            
        Returns:
            True se autenticado
        """
        name, username, auth_status = self.check_authentication()
        
        if not auth_status:
            st.warning("⚠️ Acesso restrito. Faça login para continuar.")
            self.login(auth_method=auth_method)
            return False
            
        return True
        
    def require_role(self, required_roles: List[str]) -> bool:
        """Verifica se usuário tem função necessária"""
        if not self.require_authentication():
            return False
            
        user_role = st.session_state.get('user_role', 'user')
        if user_role not in required_roles:
            st.error(f"🚫 Acesso negado. Função necessária: {', '.join(required_roles)}")
            return False
            
        return True

def create_environment_config() -> Dict:
    """
    Cria configuração baseada em variáveis de ambiente
    Útil para deployment em produção
    """
    import os
    
    config = {
        'local': None,
        'azure': None
    }
    
    # Configuração Azure AD via variáveis de ambiente
    azure_client_id = os.getenv('AZURE_CLIENT_ID')
    if azure_client_id:
        config['azure'] = {
            'client_id': azure_client_id,
            'client_secret': os.getenv('AZURE_CLIENT_SECRET'),
            'tenant_id': os.getenv('AZURE_TENANT_ID', 'common'),
            'redirect_uri': os.getenv('AZURE_REDIRECT_URI', 'http://localhost:8501'),
            'scopes': ['User.Read', 'Group.Read.All']
        }
    
    # Configuração local via variáveis de ambiente
    local_users = os.getenv('LOCAL_USERS_JSON')
    if local_users:
        try:
            import json
            users_data = json.loads(local_users)
            config['local'] = {
                'credentials': {'usernames': users_data},
                'cookie': {
                    'name': 'risk_management_auth',
                    'key': os.getenv('COOKIE_SECRET', 'default_secret_key'),
                    'expiry_days': int(os.getenv('COOKIE_EXPIRY_DAYS', '30'))
                }
            }
        except:
            pass
    
    return config

# Exemplo de uso completo
def example_usage():
    """
    Exemplo de como usar os autenticadores
    """
    st.title("🛡️ Sistema de Gerenciamento de Riscos")
    
    # Configuração híbrida
    config = create_environment_config()
    
    if not config['local'] and not config['azure']:
        # Configuração de desenvolvimento
        from .authenticator import create_sample_config
        config['local'] = create_sample_config()
        config['azure'] = create_azure_config_sample()
    
    # Inicializa autenticador híbrido
    auth = HybridAuthenticator(
        local_config=config['local'],
        azure_config=config['azure']
    )
    
    # Verifica autenticação
    if auth.require_authentication():
        # Usuário autenticado - mostra conteúdo
        user_info = auth.get_user_info()
        
        # Sidebar com informações do usuário
        with st.sidebar:
            st.success(f"✅ {user_info.get('name', 'Usuário')}")
            st.info(f"📧 {user_info.get('email', 'N/A')}")
            st.info(f"🎭 {st.session_state.get('user_role', 'user')}")
            
            auth.logout()
            
        # Conteúdo principal
        st.success(f"Bem-vindo(a) ao sistema, {user_info.get('name')}!")
        
        # Exemplo de controle de acesso por função
        if auth.require_role(['admin', 'manager']):
            st.header("🔧 Área Administrativa")
            st.write("Conteúdo apenas para administradores e gerentes")
            
        st.header("📊 Dashboard de Riscos")
        st.write("Conteúdo principal do sistema...")
        
if __name__ == "__main__":
    example_usage()
