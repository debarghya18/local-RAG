import pytest
import numpy as np
from django.test import TestCase
from django.contrib.auth import get_user_model
from documents.models import Document, DocumentChunk
from embeddings.models import EmbeddingModel, DocumentEmbedding
from embeddings.embeddings import EmbeddingGenerator, EmbeddingService

User = get_user_model()

class TestEmbeddingGenerator(TestCase):
    def setUp(self):
        self.generator = EmbeddingGenerator()
    
    def test_generate_embedding(self):
        """Test single embedding generation"""
        text = "This is a test sentence for embedding generation."
        
        embedding = self.generator.generate_embedding(text)
        
        self.assertIsInstance(embedding, list)
        self.assertGreater(len(embedding), 0)
        self.assertIsInstance(embedding[0], float)
    
    def test_generate_embeddings_batch(self):
        """Test batch embedding generation"""
        texts = [
            "First test sentence.",
            "Second test sentence.",
            "Third test sentence."
        ]
        
        embeddings = self.generator.generate_embeddings_batch(texts)
        
        self.assertEqual(len(embeddings), len(texts))
        self.assertIsInstance(embeddings[0], list)
        self.assertGreater(len(embeddings[0]), 0)
    
    def test_similarity_search(self):
        """Test similarity search functionality"""
        # Create test embeddings
        query_embedding = [0.1, 0.2, 0.3, 0.4, 0.5]
        document_embeddings = [
            [0.1, 0.2, 0.3, 0.4, 0.5],  # Identical
            [0.2, 0.3, 0.4, 0.5, 0.6],  # Similar
            [0.9, 0.8, 0.7, 0.6, 0.5],  # Different
        ]
        
        results = self.generator.similarity_search(
            query_embedding, document_embeddings, top_k=2
        )
        
        self.assertEqual(len(results), 2)
        self.assertGreater(results[0]['similarity'], results[1]['similarity'])
        self.assertEqual(results[0]['rank'], 1)
        self.assertEqual(results[1]['rank'], 2)

class TestEmbeddingService(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.service = EmbeddingService()
    
    def test_create_embeddings_for_document(self):
        """Test embedding creation for document"""
        # Create document with chunks
        document = Document.objects.create(
            user=self.user,
            title="Test Document",
            file_type="txt",
            file_size=1000,
            processing_status="completed"
        )
        
        # Create chunks
        chunks = []
        for i in range(3):
            chunk = DocumentChunk.objects.create(
                document=document,
                chunk_index=i,
                content=f"This is test chunk {i} content."
            )
            chunks.append(chunk)
        
        # Create embeddings
        embeddings = self.service.create_embeddings_for_document(document)
        
        self.assertEqual(len(embeddings), 3)
        self.assertIsInstance(embeddings[0], DocumentEmbedding)
        
        # Check that embeddings are saved
        saved_embeddings = DocumentEmbedding.objects.filter(document=document)
        self.assertEqual(saved_embeddings.count(), 3)
    
    def test_search_similar_chunks(self):
        """Test similar chunk search"""
        # Create document with chunks
        document = Document.objects.create(
            user=self.user,
            title="Test Document",
            file_type="txt",
            file_size=1000,
            processing_status="completed"
        )
        
        # Create chunks
        chunk1 = DocumentChunk.objects.create(
            document=document,
            chunk_index=0,
            content="Machine learning is a subset of artificial intelligence."
        )
        
        chunk2 = DocumentChunk.objects.create(
            document=document,
            chunk_index=1,
            content="Deep learning uses neural networks."
        )
        
        # Create embeddings
        self.service.create_embeddings_for_document(document)
        
        # Search for similar chunks
        results = self.service.search_similar_chunks(
            "What is machine learning?",
            document_ids=[str(document.id)],
            top_k=2
        )
        
        self.assertGreater(len(results), 0)
        self.assertIn('document_id', results[0])
        self.assertIn('similarity_score', results[0])
        self.assertIn('content', results[0])