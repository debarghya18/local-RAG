import logging
from celery import shared_task
from django.utils import timezone
from documents.models import Document
from .embeddings import EmbeddingService

logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3)
def generate_embeddings_for_document(self, document_id: str):
    """Generate embeddings for document chunks"""
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
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=2 ** self.request.retries, exc=e)
        raise

@shared_task
def update_embeddings_batch():
    """Update embeddings for documents that don't have them"""
    documents_without_embeddings = Document.objects.filter(
        processing_status='completed',
        embeddings__isnull=True
    ).distinct()
    
    for document in documents_without_embeddings:
        generate_embeddings_for_document.delay(str(document.id))
    
    logger.info(f"Queued embedding generation for {len(documents_without_embeddings)} documents")
    return len(documents_without_embeddings)