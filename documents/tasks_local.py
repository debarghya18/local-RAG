"""
Local version of document tasks without Celery
"""
import logging
from django.utils import timezone
from .models import Document
from .processors import DocumentProcessor
from embeddings.tasks_local import generate_embeddings_for_document_sync

logger = logging.getLogger(__name__)

def process_document_sync(document_id: str):
    """Process document synchronously for local development"""
    try:
        document = Document.objects.get(id=document_id)
        processor = DocumentProcessor()
        
        # Process document and create chunks
        chunks = processor.process_document(document)
        
        # Generate embeddings for chunks
        generate_embeddings_for_document_sync(document_id)
        
        logger.info(f"Document {document_id} processed successfully with {len(chunks)} chunks")
        
        return {
            'document_id': document_id,
            'chunks_created': len(chunks),
            'status': 'completed'
        }
        
    except Document.DoesNotExist:
        logger.error(f"Document {document_id} not found")
        raise
    except Exception as e:
        logger.error(f"Error processing document {document_id}: {str(e)}")
        # Mark document as failed
        try:
            document = Document.objects.get(id=document_id)
            document.processing_status = 'failed'
            document.save()
        except Document.DoesNotExist:
            pass
        raise