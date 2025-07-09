import streamlit as st
import requests
import json
import time
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go
from typing import Dict, List, Any, Optional

# Configure Streamlit
st.set_page_config(
    page_title="IntelliDocs - Intelligent Document Processing",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for beautiful UI
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    
    .main-header h1 {
        color: white;
        text-align: center;
        margin-bottom: 0.5rem;
    }
    
    .main-header p {
        color: white;
        text-align: center;
        opacity: 0.9;
    }
    
    .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        margin-bottom: 1rem;
    }
    
    .chat-message {
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 10px;
        max-width: 80%;
    }
    
    .user-message {
        background: #e3f2fd;
        margin-left: auto;
        text-align: right;
    }
    
    .assistant-message {
        background: #f5f5f5;
        margin-right: auto;
    }
    
    .document-card {
        background: white;
        padding: 1rem;
        border-radius: 8px;
        border: 1px solid #e0e0e0;
        margin-bottom: 1rem;
    }
    
    .status-badge {
        padding: 0.3rem 0.8rem;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: bold;
    }
    
    .status-completed {
        background: #e8f5e8;
        color: #2e7d32;
    }
    
    .status-processing {
        background: #fff3e0;
        color: #f57c00;
    }
    
    .status-failed {
        background: #ffebee;
        color: #c62828;
    }
    
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 5px;
        padding: 0.5rem 1rem;
        font-weight: 500;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }
</style>
""", unsafe_allow_html=True)

# Configuration
BACKEND_URL = "http://localhost:8000"

class IntelliDocsApp:
    def __init__(self):
        self.backend_url = BACKEND_URL
        self.init_session_state()
    
    def init_session_state(self):
        """Initialize session state variables"""
        if 'authenticated' not in st.session_state:
            st.session_state.authenticated = False
        if 'user_token' not in st.session_state:
            st.session_state.user_token = None
        if 'user_info' not in st.session_state:
            st.session_state.user_info = None
        if 'current_session' not in st.session_state:
            st.session_state.current_session = None
        if 'chat_history' not in st.session_state:
            st.session_state.chat_history = []
    
    def api_request(self, method: str, endpoint: str, data: Dict = None, files: Dict = None) -> Dict:
        """Make API request to backend"""
        url = f"{self.backend_url}/api/{endpoint}"
        headers = {}
        
        if st.session_state.user_token:
            headers['Authorization'] = f'Bearer {st.session_state.user_token}'
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers)
            elif method == 'POST':
                if files:
                    response = requests.post(url, headers=headers, data=data, files=files)
                else:
                    headers['Content-Type'] = 'application/json'
                    response = requests.post(url, headers=headers, json=data)
            elif method == 'PUT':
                headers['Content-Type'] = 'application/json'
                response = requests.put(url, headers=headers, json=data)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers)
            
            if response.status_code == 401:
                st.session_state.authenticated = False
                st.session_state.user_token = None
                st.rerun()
            
            return {
                'success': response.status_code < 400,
                'data': response.json() if response.content else {},
                'status_code': response.status_code
            }
        except Exception as e:
            return {
                'success': False,
                'data': {'error': str(e)},
                'status_code': 500
            }
    
    def render_header(self):
        """Render main header"""
        st.markdown("""
        <div class="main-header">
            <h1>📚 IntelliDocs</h1>
            <p>Intelligent Document Processing & RAG System</p>
        </div>
        """, unsafe_allow_html=True)
    
    def render_auth_page(self):
        """Render authentication page"""
        self.render_header()
        
        tab1, tab2 = st.tabs(["Login", "Register"])
        
        with tab1:
            st.subheader("Login to Your Account")
            
            with st.form("login_form"):
                email = st.text_input("Email")
                password = st.text_input("Password", type="password")
                submitted = st.form_submit_button("Login")
                
                if submitted:
                    response = self.api_request('POST', 'auth/login/', {
                        'email': email,
                        'password': password
                    })
                    
                    if response['success']:
                        st.session_state.authenticated = True
                        st.session_state.user_token = response['data']['token']
                        st.session_state.user_info = response['data']['user']
                        st.success("Login successful!")
                        st.rerun()
                    else:
                        st.error(f"Login failed: {response['data'].get('error', 'Unknown error')}")
        
        with tab2:
            st.subheader("Create New Account")
            
            with st.form("register_form"):
                email = st.text_input("Email")
                password = st.text_input("Password", type="password")
                first_name = st.text_input("First Name")
                last_name = st.text_input("Last Name")
                submitted = st.form_submit_button("Register")
                
                if submitted:
                    response = self.api_request('POST', 'auth/register/', {
                        'email': email,
                        'password': password,
                        'first_name': first_name,
                        'last_name': last_name
                    })
                    
                    if response['success']:
                        st.session_state.authenticated = True
                        st.session_state.user_token = response['data']['token']
                        st.session_state.user_info = response['data']['user']
                        st.success("Registration successful!")
                        st.rerun()
                    else:
                        st.error(f"Registration failed: {response['data'].get('error', 'Unknown error')}")
    
    def render_sidebar(self):
        """Render sidebar with user info and navigation"""
        with st.sidebar:
            st.markdown("### User Info")
            if st.session_state.user_info:
                st.write(f"**{st.session_state.user_info['first_name']} {st.session_state.user_info['last_name']}**")
                st.write(f"Email: {st.session_state.user_info['email']}")
                
                if st.button("Logout"):
                    st.session_state.authenticated = False
                    st.session_state.user_token = None
                    st.session_state.user_info = None
                    st.rerun()
            
            st.markdown("---")
            
            # Navigation
            st.markdown("### Navigation")
            page = st.radio("Go to", [
                "Dashboard",
                "Documents",
                "RAG Sessions",
                "Upload Document",
                "Settings"
            ])
            
            return page
    
    def render_dashboard(self):
        """Render dashboard with metrics and overview"""
        st.header("📊 Dashboard")
        
        # Get user stats
        docs_response = self.api_request('GET', 'documents/')
        sessions_response = self.api_request('GET', 'rag-sessions/')
        
        if docs_response['success'] and sessions_response['success']:
            documents = docs_response['data']['results'] if 'results' in docs_response['data'] else docs_response['data']
            sessions = sessions_response['data']['results'] if 'results' in sessions_response['data'] else sessions_response['data']
            
            # Metrics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Documents", len(documents))
            
            with col2:
                completed_docs = len([d for d in documents if d['processing_status'] == 'completed'])
                st.metric("Processed Documents", completed_docs)
            
            with col3:
                st.metric("RAG Sessions", len(sessions))
            
            with col4:
                processing_docs = len([d for d in documents if d['processing_status'] == 'processing'])
                st.metric("Processing", processing_docs)
            
            # Charts
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Document Processing Status")
                status_counts = {}
                for doc in documents:
                    status = doc['processing_status']
                    status_counts[status] = status_counts.get(status, 0) + 1
                
                if status_counts:
                    fig = px.pie(
                        values=list(status_counts.values()),
                        names=list(status_counts.keys()),
                        title="Document Status Distribution"
                    )
                    st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                st.subheader("Recent Activity")
                recent_docs = sorted(documents, key=lambda x: x['created_at'], reverse=True)[:5]
                
                for doc in recent_docs:
                    status_class = f"status-{doc['processing_status']}"
                    st.markdown(f"""
                    <div class="document-card">
                        <strong>{doc['title']}</strong>
                        <span class="status-badge {status_class}">{doc['processing_status']}</span>
                        <br>
                        <small>Created: {doc['created_at'][:10]}</small>
                    </div>
                    """, unsafe_allow_html=True)
    
    def render_documents(self):
        """Render documents page"""
        st.header("📄 Documents")
        
        # Get documents
        response = self.api_request('GET', 'documents/')
        
        if response['success']:
            documents = response['data']['results'] if 'results' in response['data'] else response['data']
            
            if not documents:
                st.info("No documents found. Upload your first document to get started!")
                return
            
            # Search and filter
            col1, col2 = st.columns([3, 1])
            with col1:
                search_term = st.text_input("Search documents...")
            with col2:
                status_filter = st.selectbox("Filter by status", ["all", "completed", "processing", "failed"])
            
            # Filter documents
            filtered_docs = documents
            if search_term:
                filtered_docs = [d for d in filtered_docs if search_term.lower() in d['title'].lower()]
            if status_filter != "all":
                filtered_docs = [d for d in filtered_docs if d['processing_status'] == status_filter]
            
            # Display documents
            for doc in filtered_docs:
                with st.expander(f"📄 {doc['title']}"):
                    col1, col2 = st.columns([2, 1])
                    
                    with col1:
                        st.write(f"**Description:** {doc['description'] or 'No description'}")
                        st.write(f"**Type:** {doc['file_type'].upper()}")
                        st.write(f"**Size:** {doc['file_size']:,} bytes")
                        st.write(f"**Created:** {doc['created_at'][:10]}")
                        st.write(f"**Status:** {doc['processing_status']}")
                    
                    with col2:
                        if doc['processing_status'] == 'completed':
                            if st.button(f"View Chunks", key=f"chunks_{doc['id']}"):
                                self.show_document_chunks(doc['id'])
                        
                        if doc['processing_status'] == 'failed':
                            if st.button(f"Reprocess", key=f"reprocess_{doc['id']}"):
                                reprocess_response = self.api_request('POST', f"documents/{doc['id']}/reprocess/")
                                if reprocess_response['success']:
                                    st.success("Document reprocessing started!")
                                    st.rerun()
                                else:
                                    st.error("Failed to reprocess document")
    
    def show_document_chunks(self, document_id: str):
        """Show document chunks"""
        response = self.api_request('GET', f'documents/{document_id}/chunks/')
        
        if response['success']:
            chunks = response['data']['results'] if 'results' in response['data'] else response['data']
            
            st.subheader(f"Document Chunks ({len(chunks)} chunks)")
            
            for chunk in chunks:
                with st.expander(f"Chunk {chunk['chunk_index']}"):
                    st.write(chunk['content'])
                    if chunk['metadata']:
                        st.json(chunk['metadata'])
    
    def render_rag_sessions(self):
        """Render RAG sessions page"""
        st.header("🤖 RAG Sessions")
        
        # Get sessions
        response = self.api_request('GET', 'rag-sessions/')
        
        if response['success']:
            sessions = response['data']['results'] if 'results' in response['data'] else response['data']
            
            # Create new session
            with st.expander("Create New Session"):
                with st.form("new_session_form"):
                    title = st.text_input("Session Title")
                    
                    # Get user documents
                    docs_response = self.api_request('GET', 'documents/')
                    if docs_response['success']:
                        documents = docs_response['data']['results'] if 'results' in docs_response['data'] else docs_response['data']
                        completed_docs = [d for d in documents if d['processing_status'] == 'completed']
                        
                        if completed_docs:
                            selected_docs = st.multiselect(
                                "Select Documents",
                                options=[d['id'] for d in completed_docs],
                                format_func=lambda x: next(d['title'] for d in completed_docs if d['id'] == x)
                            )
                            
                            if st.form_submit_button("Create Session"):
                                if title and selected_docs:
                                    create_response = self.api_request('POST', 'rag-sessions/', {
                                        'title': title,
                                        'document_ids': selected_docs
                                    })
                                    
                                    if create_response['success']:
                                        st.success("Session created successfully!")
                                        st.rerun()
                                    else:
                                        st.error("Failed to create session")
                                else:
                                    st.warning("Please provide title and select documents")
                        else:
                            st.info("No completed documents available. Please upload and process documents first.")
            
            # Display sessions
            if sessions:
                for session in sessions:
                    with st.expander(f"🤖 {session['title']}"):
                        st.write(f"**Documents:** {len(session['documents'])}")
                        st.write(f"**Created:** {session['created_at'][:10]}")
                        
                        col1, col2 = st.columns([3, 1])
                        
                        with col1:
                            if st.button(f"Start Chat", key=f"chat_{session['id']}"):
                                st.session_state.current_session = session
                                st.rerun()
                        
                        with col2:
                            if st.button(f"View History", key=f"history_{session['id']}"):
                                self.show_session_history(session['id'])
            else:
                st.info("No RAG sessions found. Create your first session to get started!")
        
        # Chat interface
        if st.session_state.current_session:
            self.render_chat_interface()
    
    def render_chat_interface(self):
        """Render chat interface for RAG session"""
        session = st.session_state.current_session
        
        st.markdown("---")
        st.subheader(f"💬 Chat - {session['title']}")
        
        # Chat history
        chat_container = st.container()
        
        with chat_container:
            for message in st.session_state.chat_history:
                if message['role'] == 'user':
                    st.markdown(f"""
                    <div class="chat-message user-message">
                        <strong>You:</strong> {message['content']}
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div class="chat-message assistant-message">
                        <strong>IntelliDocs:</strong> {message['content']}
                    </div>
                    """, unsafe_allow_html=True)
        
        # Query input
        with st.form("chat_form", clear_on_submit=True):
            query = st.text_input("Ask a question about your documents...")
            submitted = st.form_submit_button("Send")
            
            if submitted and query:
                # Add user message to history
                st.session_state.chat_history.append({
                    'role': 'user',
                    'content': query
                })
                
                # Process query
                with st.spinner("Processing your question..."):
                    response = self.api_request('POST', 'query/', {
                        'session_id': session['id'],
                        'query_text': query
                    })
                
                if response['success']:
                    # Add assistant response to history
                    st.session_state.chat_history.append({
                        'role': 'assistant',
                        'content': response['data']['response_text']
                    })
                    
                    # Show sources
                    if response['data']['sources']:
                        st.subheader("Sources")
                        for source in response['data']['sources']:
                            st.write(f"📄 **{source['document_title']}** (Similarity: {source['similarity_score']:.2f})")
                            st.write(source['preview'])
                            st.markdown("---")
                    
                    st.rerun()
                else:
                    st.error("Failed to process query")
        
        # Clear chat button
        if st.button("Clear Chat"):
            st.session_state.chat_history = []
            st.rerun()
        
        # Back to sessions
        if st.button("← Back to Sessions"):
            st.session_state.current_session = None
            st.rerun()
    
    def show_session_history(self, session_id: str):
        """Show session query history"""
        response = self.api_request('GET', f'rag-sessions/{session_id}/queries/')
        
        if response['success']:
            queries = response['data']['results'] if 'results' in response['data'] else response['data']
            
            if queries:
                st.subheader("Query History")
                for query in queries:
                    with st.expander(f"Q: {query['query_text'][:50]}..."):
                        st.write(f"**Question:** {query['query_text']}")
                        st.write(f"**Response:** {query['response_text']}")
                        st.write(f"**Processing Time:** {query['processing_time']:.2f}s")
                        st.write(f"**Date:** {query['created_at'][:10]}")
                        
                        if query['sources']:
                            st.write("**Sources:**")
                            for source in query['sources']:
                                st.write(f"- {source['document_title']} (Score: {source['similarity_score']:.2f})")
            else:
                st.info("No queries found for this session")
    
    def render_upload_document(self):
        """Render document upload page"""
        st.header("📤 Upload Document")
        
        with st.form("upload_form"):
            title = st.text_input("Document Title")
            description = st.text_area("Description (Optional)")
            uploaded_file = st.file_uploader(
                "Choose a file",
                type=['pdf', 'docx', 'txt'],
                help="Supported formats: PDF, DOCX, TXT (Max 100MB)"
            )
            
            if st.form_submit_button("Upload"):
                if title and uploaded_file:
                    with st.spinner("Uploading and processing document..."):
                        files = {'file': uploaded_file}
                        data = {
                            'title': title,
                            'description': description
                        }
                        
                        response = self.api_request('POST', 'upload/', data, files)
                        
                        if response['success']:
                            st.success("Document uploaded successfully! Processing will begin shortly.")
                            st.json(response['data'])
                        else:
                            st.error(f"Upload failed: {response['data'].get('error', 'Unknown error')}")
                else:
                    st.warning("Please provide a title and select a file")
    
    def render_settings(self):
        """Render settings page"""
        st.header("⚙️ Settings")
        
        # User profile
        st.subheader("User Profile")
        user_info = st.session_state.user_info
        
        with st.form("profile_form"):
            first_name = st.text_input("First Name", value=user_info.get('first_name', ''))
            last_name = st.text_input("Last Name", value=user_info.get('last_name', ''))
            
            if st.form_submit_button("Update Profile"):
                response = self.api_request('PUT', 'auth/me/', {
                    'first_name': first_name,
                    'last_name': last_name
                })
                
                if response['success']:
                    st.session_state.user_info = response['data']
                    st.success("Profile updated successfully!")
                else:
                    st.error("Failed to update profile")
        
        # RAG Configuration
        st.subheader("RAG Configuration")
        
        with st.form("rag_config_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                chunk_size = st.number_input("Chunk Size", min_value=100, max_value=2000, value=1000)
                chunk_overlap = st.number_input("Chunk Overlap", min_value=0, max_value=500, value=200)
                top_k = st.number_input("Top K Results", min_value=1, max_value=50, value=10)
            
            with col2:
                temperature = st.slider("Temperature", min_value=0.0, max_value=1.0, value=0.7)
                similarity_threshold = st.slider("Similarity Threshold", min_value=0.0, max_value=1.0, value=0.5)
                max_tokens = st.number_input("Max Tokens", min_value=512, max_value=4096, value=2048)
            
            if st.form_submit_button("Save Configuration"):
                st.success("Configuration saved! (This would update the backend)")
    
    def run(self):
        """Main application entry point"""
        if not st.session_state.authenticated:
            self.render_auth_page()
        else:
            self.render_header()
            
            # Get current page from sidebar
            page = self.render_sidebar()
            
            # Render selected page
            if page == "Dashboard":
                self.render_dashboard()
            elif page == "Documents":
                self.render_documents()
            elif page == "RAG Sessions":
                self.render_rag_sessions()
            elif page == "Upload Document":
                self.render_upload_document()
            elif page == "Settings":
                self.render_settings()

# Run the application
if __name__ == "__main__":
    app = IntelliDocsApp()
    app.run()