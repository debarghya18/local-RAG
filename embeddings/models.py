from django.db import models
from django.contrib.auth import get_user_model
from documents.models import Document, DocumentChunk
import uuid

User = get_user_model()

class EmbeddingModel(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    model_path = models.CharField(max_length=255)
    dimension = models.IntegerField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'embedding_models'
    
    def __str__(self):
        return self.name

class DocumentEmbedding(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='embeddings')
    chunk = models.ForeignKey(DocumentChunk, on_delete=models.CASCADE, related_name='embeddings')
    embedding_model = models.ForeignKey(EmbeddingModel, on_delete=models.CASCADE)
    embedding_vector = models.JSONField()  # Store as JSON array
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'document_embeddings'
        unique_together = ['chunk', 'embedding_model']
    
    def __str__(self):
        return f"Embedding for {self.document.title} - Chunk {self.chunk.chunk_index}"

class VectorStore(models.Model):
    STORE_TYPES = [
        ('faiss', 'FAISS'),
        ('chroma', 'Chroma'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='vector_stores')
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    store_type = models.CharField(max_length=20, choices=STORE_TYPES)
    embedding_model = models.ForeignKey(EmbeddingModel, on_delete=models.CASCADE)
    index_path = models.CharField(max_length=255)
    document_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'vector_stores'
        unique_together = ['user', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.store_type})"

class SearchQuery(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='search_queries')
    vector_store = models.ForeignKey(VectorStore, on_delete=models.CASCADE, related_name='queries')
    query_text = models.TextField()
    query_embedding = models.JSONField()
    results_count = models.IntegerField()
    response_time = models.FloatField()  # in seconds
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'search_queries'
        ordering = ['-created_at']

class SearchResult(models.Model):
    query = models.ForeignKey(SearchQuery, on_delete=models.CASCADE, related_name='results')
    document = models.ForeignKey(Document, on_delete=models.CASCADE)
    chunk = models.ForeignKey(DocumentChunk, on_delete=models.CASCADE)
    similarity_score = models.FloatField()
    rank = models.IntegerField()
    
    class Meta:
        db_table = 'search_results'
        ordering = ['rank']