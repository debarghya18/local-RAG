"""
Local version of embedding tasks without Celery
"""
import logging
from documents.models import Document
from .embeddings import EmbeddingService

logger = logging.getLogger(__name__)

def generate_embeddings_for_document_sync(document_id: str):
    """Generate embeddings for document chunks synchronously"""
    try:
        document = Document.objects.get(id=document_id)
        service = EmbeddingService()
        
        # Create embeddings
        embeddings = service.create_embeddings_for_document(document)
        
        logger.info(f"Generated {len(embeddings)} embeddings for document {document_id}")
        
        return {
            'document_id': document_id,
            'embeddings_created': len(embeddings),
            'status': 'completed'
        }
        
    except Document.DoesNotExist:
        logger.error(f"Document {document_id} not found")
        raise
    except Exception as e:
        logger.error(f"Error generating embeddings for document {document_id}: {str(e)}")
        raise