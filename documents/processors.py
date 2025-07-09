import os
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
import PyPDF2
import docx
import spacy
from django.core.files.uploadedfile import UploadedFile
from .models import Document, DocumentChunk

logger = logging.getLogger(__name__)

class DocumentProcessor:
    def __init__(self):
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            logger.error("Spacy model not found. Please install: python -m spacy download en_core_web_sm")
            self.nlp = None
    
    def process_document(self, document: Document) -> List[DocumentChunk]:
        """Process document and create chunks"""
        try:
            document.processing_status = 'processing'
            document.save()
            
            # Extract text based on file type
            if document.file_type == 'pdf':
                text = self._extract_pdf_text(document.file)
            elif document.file_type == 'docx':
                text = self._extract_docx_text(document.file)
            elif document.file_type == 'txt':
                text = self._extract_txt_text(document.file)
            else:
                raise ValueError(f"Unsupported file type: {document.file_type}")
            
            # Create chunks
            chunks = self._create_chunks(text, document)
            
            document.processing_status = 'completed'
            document.save()
            
            return chunks
            
        except Exception as e:
            logger.error(f"Error processing document {document.id}: {str(e)}")
            document.processing_status = 'failed'
            document.save()
            raise
    
    def _extract_pdf_text(self, file) -> str:
        """Extract text from PDF file"""
        text = ""
        try:
            pdf_reader = PyPDF2.PdfReader(file)
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
        except Exception as e:
            logger.error(f"Error extracting PDF text: {str(e)}")
            raise
        return text
    
    def _extract_docx_text(self, file) -> str:
        """Extract text from DOCX file"""
        try:
            doc = docx.Document(file)
            text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
        except Exception as e:
            logger.error(f"Error extracting DOCX text: {str(e)}")
            raise
        return text
    
    def _extract_txt_text(self, file) -> str:
        """Extract text from TXT file"""
        try:
            text = file.read().decode('utf-8')
        except Exception as e:
            logger.error(f"Error extracting TXT text: {str(e)}")
            raise
        return text
    
    def _create_chunks(self, text: str, document: Document, chunk_size: int = 1000, overlap: int = 200) -> List[DocumentChunk]:
        """Create text chunks from document text"""
        chunks = []
        words = text.split()
        
        for i in range(0, len(words), chunk_size - overlap):
            chunk_words = words[i:i + chunk_size]
            chunk_text = ' '.join(chunk_words)
            
            if len(chunk_text.strip()) > 0:
                # Extract metadata using spaCy if available
                metadata = self._extract_chunk_metadata(chunk_text)
                
                chunk = DocumentChunk.objects.create(
                    document=document,
                    chunk_index=len(chunks),
                    content=chunk_text,
                    metadata=metadata
                )
                chunks.append(chunk)
        
        return chunks
    
    def _extract_chunk_metadata(self, text: str) -> Dict[str, Any]:
        """Extract metadata from text chunk using NLP"""
        metadata = {
            'word_count': len(text.split()),
            'character_count': len(text),
        }
        
        if self.nlp:
            try:
                doc = self.nlp(text)
                metadata.update({
                    'entities': [{'text': ent.text, 'label': ent.label_} for ent in doc.ents],
                    'sentences': len(list(doc.sents)),
                    'tokens': len(doc),
                })
            except Exception as e:
                logger.warning(f"Error extracting NLP metadata: {str(e)}")
        
        return metadata

class DocumentValidator:
    @staticmethod
    def validate_file(file: UploadedFile) -> Dict[str, Any]:
        """Validate uploaded file"""
        errors = []
        
        # Check file size (100MB max)
        if file.size > 100 * 1024 * 1024:
            errors.append("File size exceeds 100MB limit")
        
        # Check file type
        allowed_extensions = ['.pdf', '.docx', '.txt']
        file_extension = os.path.splitext(file.name)[1].lower()
        
        if file_extension not in allowed_extensions:
            errors.append(f"File type {file_extension} not supported")
        
        # Check file content
        if file.size == 0:
            errors.append("File is empty")
        
        return {
            'is_valid': len(errors) == 0,
            'errors': errors,
            'file_type': file_extension[1:] if file_extension else None,
            'file_size': file.size,
        }