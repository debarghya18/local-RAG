from django.db import models
from django.contrib.auth import get_user_model
from documents.models import Document
import uuid

User = get_user_model()

class RAGSession(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='rag_sessions')
    title = models.CharField(max_length=255)
    documents = models.ManyToManyField(Document, related_name='rag_sessions')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'rag_sessions'
        ordering = ['-updated_at']
    
    def __str__(self):
        return self.title

class RAGQuery(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.ForeignKey(RAGSession, on_delete=models.CASCADE, related_name='queries')
    query_text = models.TextField()
    response_text = models.TextField()
    sources = models.JSONField(default=list)  # Store source chunks
    metadata = models.JSONField(default=dict)
    processing_time = models.FloatField()  # in seconds
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'rag_queries'
        ordering = ['-created_at']

class RAGConfiguration(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='rag_config')
    model_name = models.CharField(max_length=100, default='all-MiniLM-L6-v2')
    chunk_size = models.IntegerField(default=1000)
    chunk_overlap = models.IntegerField(default=200)
    max_tokens = models.IntegerField(default=2048)
    temperature = models.FloatField(default=0.7)
    top_k = models.IntegerField(default=10)
    similarity_threshold = models.FloatField(default=0.5)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'rag_configurations'