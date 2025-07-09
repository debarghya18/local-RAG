import logging
import time
from typing import List, Dict, Any, Optional
from django.contrib.auth import get_user_model
from documents.models import Document
from embeddings.embeddings import EmbeddingService
from .models import RAGSession, RAGQuery, RAGConfiguration

logger = logging.getLogger(__name__)

User = get_user_model()

class RAGPipeline:
    def __init__(self, user):
        self.user = user
        self.embedding_service = EmbeddingService()
        self.config = self._get_user_config()
    
    def _get_user_config(self) -> RAGConfiguration:
        """Get user's RAG configuration"""
        config, created = RAGConfiguration.objects.get_or_create(
            user=self.user,
            defaults={
                'model_name': 'all-MiniLM-L6-v2',
                'chunk_size': 1000,
                'chunk_overlap': 200,
                'max_tokens': 2048,
                'temperature': 0.7,
                'top_k': 10,
                'similarity_threshold': 0.5,
            }
        )
        return config
    
    def create_session(self, title: str, document_ids: List[str]) -> RAGSession:
        """Create a new RAG session"""
        try:
            session = RAGSession.objects.create(
                user=self.user,
                title=title
            )
            
            # Add documents to session
            documents = Document.objects.filter(
                id__in=document_ids,
                user=self.user
            )
            session.documents.set(documents)
            
            logger.info(f"Created RAG session {session.id} with {len(documents)} documents")
            return session
            
        except Exception as e:
            logger.error(f"Error creating RAG session: {str(e)}")
            raise
    
    def process_query(self, session: RAGSession, query_text: str) -> RAGQuery:
        """Process a query using RAG pipeline"""
        start_time = time.time()
        
        try:
            # Get document IDs from session
            document_ids = list(session.documents.values_list('id', flat=True))
            
            # Search for similar chunks
            similar_chunks = self.embedding_service.search_similar_chunks(
                query=query_text,
                document_ids=[str(doc_id) for doc_id in document_ids],
                top_k=self.config.top_k
            )
            
            # Filter by similarity threshold
            filtered_chunks = [
                chunk for chunk in similar_chunks
                if chunk['similarity_score'] >= self.config.similarity_threshold
            ]
            
            # Generate response
            response_text = self._generate_response(query_text, filtered_chunks)
            
            # Create query record
            processing_time = time.time() - start_time
            
            query = RAGQuery.objects.create(
                session=session,
                query_text=query_text,
                response_text=response_text,
                sources=self._format_sources(filtered_chunks),
                metadata={
                    'chunks_found': len(similar_chunks),
                    'chunks_used': len(filtered_chunks),
                    'config': {
                        'top_k': self.config.top_k,
                        'similarity_threshold': self.config.similarity_threshold,
                        'model_name': self.config.model_name,
                    }
                },
                processing_time=processing_time
            )
            
            logger.info(f"Processed query in {processing_time:.2f}s with {len(filtered_chunks)} sources")
            return query
            
        except Exception as e:
            logger.error(f"Error processing query: {str(e)}")
            raise
    
    def _generate_response(self, query: str, context_chunks: List[Dict[str, Any]]) -> str:
        """Generate response using context chunks"""
        try:
            if not context_chunks:
                return "I couldn't find relevant information in the provided documents to answer your question."
            
            # Create context from top chunks
            context = "\n\n".join([
                f"From {chunk['document_title']} (similarity: {chunk['similarity_score']:.2f}):\n{chunk['content'][:500]}..."
                for chunk in context_chunks[:5]  # Use top 5 chunks
            ])
            
            # Simple response generation (in production, you'd use a proper LLM)
            response = f"""Based on the provided documents, here's what I found regarding your question: "{query}"

{context}

This information is compiled from {len(context_chunks)} relevant sections across your documents."""
            
            return response
            
        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            return "I encountered an error while generating the response. Please try again."
    
    def _format_sources(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Format source information for frontend display"""
        sources = []
        for chunk in chunks:
            sources.append({
                'document_id': chunk['document_id'],
                'document_title': chunk['document_title'],
                'chunk_id': chunk['chunk_id'],
                'chunk_index': chunk['chunk_index'],
                'similarity_score': chunk['similarity_score'],
                'rank': chunk['rank'],
                'preview': chunk['content'][:200] + "..." if len(chunk['content']) > 200 else chunk['content']
            })
        return sources
    
    def get_session_history(self, session: RAGSession) -> List[RAGQuery]:
        """Get query history for a session"""
        return session.queries.all()
    
    def update_config(self, **kwargs) -> RAGConfiguration:
        """Update user's RAG configuration"""
        try:
            for key, value in kwargs.items():
                if hasattr(self.config, key):
                    setattr(self.config, key, value)
            
            self.config.save()
            logger.info(f"Updated RAG configuration for user {self.user.id}")
            return self.config
            
        except Exception as e:
            logger.error(f"Error updating RAG config: {str(e)}")
            raise

class RAGService:
    @staticmethod
    def get_user_sessions(user) -> List[RAGSession]:
        """Get all RAG sessions for a user"""
        return RAGSession.objects.filter(user=user)
    
    @staticmethod
    def get_session_by_id(session_id: str, user) -> Optional[RAGSession]:
        """Get RAG session by ID"""
        try:
            return RAGSession.objects.get(id=session_id, user=user)
        except RAGSession.DoesNotExist:
            return None
    
    @staticmethod
    def delete_session(session_id: str, user) -> bool:
        """Delete RAG session"""
        try:
            session = RAGSession.objects.get(id=session_id, user=user)
            session.delete()
            return True
        except RAGSession.DoesNotExist:
            return False