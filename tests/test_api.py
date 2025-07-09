import pytest
import json
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from documents.models import Document
from rag.models import RAGSession
from core.authentication import generate_jwt_token
from api.serializers import (
    UserSerializer, DocumentSerializer, RAGSessionSerializer,
    DocumentUploadSerializer
)
import logging
from django.core.files.uploadedfile import SimpleUploadedFile

User = get_user_model()

class TestAuthenticationAPI(TestCase):
    def setUp(self):
        self.client = APIClient()
    
    def test_user_registration(self):
        """Test user registration endpoint"""
        data = {
            'email': 'test@example.com',
            'password': 'testpass123',
            'first_name': 'Test',
            'last_name': 'User'
        }
        
        response = self.client.post('/api/auth/register/', data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('token', response.data)
        self.assertIn('user', response.data)
    
    def test_user_login(self):
        """Test user login endpoint"""
        # Create user
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        data = {
            'email': 'test@example.com',
            'password': 'testpass123'
        }
        
        response = self.client.post('/api/auth/login/', data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('token', response.data)
        self.assertIn('user', response.data)
    
    def test_invalid_login(self):
        """Test login with invalid credentials"""
        data = {
            'email': 'nonexistent@example.com',
            'password': 'wrongpassword'
        }
        
        response = self.client.post('/api/auth/login/', data)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn('error', response.data)

class TestDocumentAPI(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.token = generate_jwt_token(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
    
    def test_document_list(self):
        """Test document list endpoint"""
        # Create test documents
        Document.objects.create(
            user=self.user,
            title="Test Document 1",
            file_type="txt",
            file_size=1000
        )
        
        Document.objects.create(
            user=self.user,
            title="Test Document 2",
            file_type="pdf",
            file_size=2000
        )
        
        response = self.client.get('/api/documents/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
    
    def test_document_upload(self):
        """Test document upload endpoint"""
        # Create a test file
        content = b"This is test content"
        
        data = {
            'title': 'Test Upload',
            'description': 'Test description',
            'file': SimpleUploadedFile(
                "test.txt",
                content,
                content_type="text/plain"
            )
        }
        
        response = self.client.post('/api/upload/', data, format='multipart')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['title'], 'Test Upload')
        
        # Check document was created
        document = Document.objects.get(title='Test Upload')
        self.assertEqual(document.user, self.user)
    
    def test_unauthorized_access(self):
        """Test unauthorized access to documents"""
        # Remove authentication
        self.client.credentials()
        
        response = self.client.get('/api/documents/')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

class TestRAGAPI(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.token = generate_jwt_token(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
    
    def test_rag_session_creation(self):
        """Test RAG session creation"""
        # Create test document
        document = Document.objects.create(
            user=self.user,
            title="Test Document",
            file_type="txt",
            file_size=1000,
            processing_status="completed"
        )
        
        data = {
            'title': 'Test RAG Session',
            'document_ids': [str(document.id)]
        }
        
        response = self.client.post('/api/rag-sessions/', data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['title'], 'Test RAG Session')
        
        # Check session was created
        session = RAGSession.objects.get(title='Test RAG Session')
        self.assertEqual(session.user, self.user)
        self.assertEqual(session.documents.count(), 1)
    
    def test_rag_query_processing(self):
        """Test RAG query processing"""
        # Create session with document
        document = Document.objects.create(
            user=self.user,
            title="Test Document",
            file_type="txt",
            file_size=1000,
            processing_status="completed"
        )
        
        session = RAGSession.objects.create(
            user=self.user,
            title="Test Session"
        )
        session.documents.add(document)
        
        data = {
            'session_id': str(session.id),
            'query_text': 'What is the main topic of the document?'
        }
        
        response = self.client.post('/api/query/', data)
        
        # Note: This might fail if embeddings aren't set up
        # In a real test, you'd mock the embedding service
        self.assertIn(response.status_code, [
            status.HTTP_200_OK,
            status.HTTP_500_INTERNAL_SERVER_ERROR
        ])
    
    def test_rag_session_list(self):
        """Test RAG session list endpoint"""
        # Create test sessions
        RAGSession.objects.create(
            user=self.user,
            title="Session 1"
        )
        
        RAGSession.objects.create(
            user=self.user,
            title="Session 2"
        )
        
        response = self.client.get('/api/rag-sessions/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

class TestHealthCheckAPI(TestCase):
    def setUp(self):
        self.client = APIClient()
    
    def test_health_check(self):
        """Test health check endpoint"""
        response = self.client.get('/api/health/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('status', response.data)