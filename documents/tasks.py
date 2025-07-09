import logging
from celery import shared_task
from django.utils import timezone
from .models import Document
from .processors import DocumentProcessor
from embeddings.tasks import generate_embeddings_for_document

logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3)
def process_document_task(self, document_id: str):
    """Process document asynchronously"""
    try:
        document = Document.objects.get(id=document_id)
        processor = DocumentProcessor()
        
        # Process document and create chunks
        chunks = processor.process_document(document)
        
        # Generate embeddings for chunks
        generate_embeddings_for_document.delay(document_id)
        
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
        if self.request.retries < self.max_retries:
            # Retry after exponential backoff
            raise self.retry(countdown=2 ** self.request.retries, exc=e)
        else:
            # Mark document as failed
            try:
                document = Document.objects.get(id=document_id)
                document.processing_status = 'failed'
                document.save()
            except Document.DoesNotExist:
                pass
            raise

@shared_task
def cleanup_failed_documents():
    """Clean up documents that failed processing"""
    failed_documents = Document.objects.filter(
        processing_status='failed',
        updated_at__lt=timezone.now() - timezone.timedelta(hours=24)
    )
    
    count = 0
    for doc in failed_documents:
        try:
            doc.delete()
            count += 1
        except Exception as e:
            logger.error(f"Error deleting failed document {doc.id}: {str(e)}")
    
    logger.info(f"Cleaned up {count} failed documents")
    return count