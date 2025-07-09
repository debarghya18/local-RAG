import logging
import numpy as np
from typing import List, Dict, Any, Optional
from sentence_transformers import SentenceTransformer
from django.conf import settings
from django.core.cache import cache
from .models import EmbeddingModel, DocumentEmbedding

logger = logging.getLogger(__name__)

class EmbeddingGenerator:
    def __init__(self, model_name: str = None):
        self.model_name = model_name or settings.EMBEDDING_MODEL
        self.model = None
        self._load_model()
    
    def _load_model(self):
        """Load the embedding model"""
        try:
            # Check if model is cached
            cache_key = f"embedding_model_{self.model_name}"
            self.model = cache.get(cache_key)
            
            if self.model is None:
                self.model = SentenceTransformer(self.model_name)
                cache.set(cache_key, self.model, timeout=3600)  # Cache for 1 hour
                
            logger.info(f"Loaded embedding model: {self.model_name}")
        except Exception as e:
            logger.error(f"Error loading embedding model: {str(e)}")
            raise
    
    def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for a single text"""
        try:
            if self.model is None:
                self._load_model()
            
            embedding = self.model.encode(text, convert_to_tensor=False)
            return embedding.tolist()
        except Exception as e:
            logger.error(f"Error generating embedding: {str(e)}")
            raise
    
    def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a batch of texts"""
        try:
            if self.model is None:
                self._load_model()
            
            embeddings = self.model.encode(texts, convert_to_tensor=False)
            return embeddings.tolist()
        except Exception as e:
            logger.error(f"Error generating batch embeddings: {str(e)}")
            raise
    
    def similarity_search(self, query_embedding: List[float], document_embeddings: List[List[float]], top_k: int = 10) -> List[Dict[str, Any]]:
        """Find most similar embeddings using cosine similarity"""
        try:
            query_vec = np.array(query_embedding)
            doc_vecs = np.array(document_embeddings)
            
            # Calculate cosine similarity
            similarities = np.dot(doc_vecs, query_vec) / (
                np.linalg.norm(doc_vecs, axis=1) * np.linalg.norm(query_vec)
            )
            
            # Get top k results
            top_indices = np.argsort(similarities)[::-1][:top_k]
            
            results = []
            for i, idx in enumerate(top_indices):
                results.append({
                    'index': int(idx),
                    'similarity': float(similarities[idx]),
                    'rank': i + 1
                })
            
            return results
        except Exception as e:
            logger.error(f"Error in similarity search: {str(e)}")
            raise

class EmbeddingService:
    def __init__(self):
        self.generator = EmbeddingGenerator()
    
    def create_embeddings_for_document(self, document) -> List[DocumentEmbedding]:
        """Create embeddings for all chunks of a document"""
        try:
            # Get or create embedding model
            embedding_model, created = EmbeddingModel.objects.get_or_create(
                name=self.generator.model_name,
                defaults={
                    'description': f'Sentence transformer model {self.generator.model_name}',
                    'model_path': self.generator.model_name,
                    'dimension': 384,  # Default dimension for all-MiniLM-L6-v2
                    'is_active': True
                }
            )
            
            # Get all chunks for the document
            chunks = document.chunks.all().order_by('chunk_index')
            
            # Generate embeddings in batches
            batch_size = 100
            embeddings_created = []
            
            for i in range(0, len(chunks), batch_size):
                batch_chunks = chunks[i:i + batch_size]
                batch_texts = [chunk.content for chunk in batch_chunks]
                
                # Generate embeddings for batch
                batch_embeddings = self.generator.generate_embeddings_batch(batch_texts)
                
                # Save embeddings
                for chunk, embedding in zip(batch_chunks, batch_embeddings):
                    doc_embedding, created = DocumentEmbedding.objects.get_or_create(
                        document=document,
                        chunk=chunk,
                        embedding_model=embedding_model,
                        defaults={'embedding_vector': embedding}
                    )
                    embeddings_created.append(doc_embedding)
            
            logger.info(f"Created {len(embeddings_created)} embeddings for document {document.id}")
            return embeddings_created
            
        except Exception as e:
            logger.error(f"Error creating embeddings for document {document.id}: {str(e)}")
            raise
    
    def search_similar_chunks(self, query: str, document_ids: List[str] = None, top_k: int = 10) -> List[Dict[str, Any]]:
        """Search for similar chunks using embeddings"""
        try:
            # Generate query embedding
            query_embedding = self.generator.generate_embedding(query)
            
            # Get document embeddings
            embeddings_query = DocumentEmbedding.objects.select_related('document', 'chunk')
            
            if document_ids:
                embeddings_query = embeddings_query.filter(document_id__in=document_ids)
            
            embeddings = list(embeddings_query)
            
            if not embeddings:
                return []
            
            # Extract embedding vectors
            embedding_vectors = [emb.embedding_vector for emb in embeddings]
            
            # Find similar embeddings
            similar_results = self.generator.similarity_search(
                query_embedding, embedding_vectors, top_k
            )
            
            # Format results
            results = []
            for result in similar_results:
                embedding_obj = embeddings[result['index']]
                results.append({
                    'document_id': str(embedding_obj.document.id),
                    'document_title': embedding_obj.document.title,
                    'chunk_id': str(embedding_obj.chunk.id),
                    'chunk_index': embedding_obj.chunk.chunk_index,
                    'content': embedding_obj.chunk.content,
                    'similarity_score': result['similarity'],
                    'rank': result['rank'],
                    'metadata': embedding_obj.chunk.metadata
                })
            
            return results
            
        except Exception as e:
            logger.error(f"Error searching similar chunks: {str(e)}")
            raise