import pytest
import tempfile
import os
from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model
from documents.models import Document, DocumentChunk
from documents.processors import DocumentProcessor, DocumentValidator

User = get_user_model()

class TestDocumentProcessor(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.processor = DocumentProcessor()
    
    def test_create_chunks(self):
        """Test text chunking functionality"""
        text = "This is a test document. " * 100
        
        # Create mock document
        document = Document.objects.create(
            user=self.user,
            title="Test Document",
            file_type="txt",
            file_size=len(text)
        )
        
        chunks = self.processor._create_chunks(text, document, chunk_size=50, overlap=10)
        
        self.assertGreater(len(chunks), 0)
        self.assertIsInstance(chunks[0], DocumentChunk)
    
    def test_extract_txt_text(self):
        """Test text extraction from TXT files"""
        content = "This is a test text file content."
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(content)
            f.flush()
            
            # Create file object
            with open(f.name, 'rb') as file:
                extracted_text = self.processor._extract_txt_text(file)
                
            self.assertEqual(extracted_text.strip(), content)
        
        # Clean up
        os.unlink(f.name)
    
    def test_extract_chunk_metadata(self):
        """Test metadata extraction from chunks"""
        text = "This is a test document with some entities like Python and Django."
        
        metadata = self.processor._extract_chunk_metadata(text)
        
        self.assertIn('word_count', metadata)
        self.assertIn('character_count', metadata)
        self.assertGreater(metadata['word_count'], 0)
        self.assertGreater(metadata['character_count'], 0)

class TestDocumentValidator(TestCase):
    def test_validate_valid_file(self):
        """Test validation of valid files"""
        # Create a valid text file
        content = b"This is valid text content."
        uploaded_file = SimpleUploadedFile(
            "test.txt", 
            content, 
            content_type="text/plain"
        )
        
        result = DocumentValidator.validate_file(uploaded_file)
        
        self.assertTrue(result['is_valid'])
        self.assertEqual(result['file_type'], 'txt')
        self.assertEqual(result['file_size'], len(content))
        self.assertEqual(len(result['errors']), 0)
    
    def test_validate_large_file(self):
        """Test validation of oversized files"""
        # Create large file (simulated)
        large_content = b"x" * (101 * 1024 * 1024)  # 101MB
        uploaded_file = SimpleUploadedFile(
            "large.txt",
            large_content,
            content_type="text/plain"
        )
        
        result = DocumentValidator.validate_file(uploaded_file)
        
        self.assertFalse(result['is_valid'])
        self.assertIn("File size exceeds 100MB limit", result['errors'])
    
    def test_validate_invalid_file_type(self):
        """Test validation of invalid file types"""
        content = b"Invalid content"
        uploaded_file = SimpleUploadedFile(
            "test.xyz",
            content,
            content_type="application/octet-stream"
        )
        
        result = DocumentValidator.validate_file(uploaded_file)
        
        self.assertFalse(result['is_valid'])
        self.assertIn("File type .xyz not supported", result['errors'])
    
    def test_validate_empty_file(self):
        """Test validation of empty files"""
        uploaded_file = SimpleUploadedFile(
            "empty.txt",
            b"",
            content_type="text/plain"
        )
        
        result = DocumentValidator.validate_file(uploaded_file)
        
        self.assertFalse(result['is_valid'])
        self.assertIn("File is empty", result['errors'])