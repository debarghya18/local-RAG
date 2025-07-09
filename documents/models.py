from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
import uuid
import os

User = get_user_model()

class Document(models.Model):
    PROCESSING_STATUS = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    FILE_TYPES = [
        ('pdf', 'PDF'),
        ('docx', 'Word Document'),
        ('txt', 'Text File'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='documents')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    file = models.FileField(upload_to='documents/')
    file_type = models.CharField(max_length=10, choices=FILE_TYPES)
    file_size = models.BigIntegerField()
    processing_status = models.CharField(max_length=20, choices=PROCESSING_STATUS, default='pending')
    processed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'documents'
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title
    
    @property
    def file_extension(self):
        return os.path.splitext(self.file.name)[1].lower()

class DocumentChunk(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='chunks')
    chunk_index = models.IntegerField()
    content = models.TextField()
    metadata = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'document_chunks'
        ordering = ['chunk_index']
        unique_together = ['document', 'chunk_index']

class DocumentMetadata(models.Model):
    document = models.OneToOneField(Document, on_delete=models.CASCADE, related_name='metadata')
    author = models.CharField(max_length=255, blank=True)
    subject = models.CharField(max_length=255, blank=True)
    keywords = models.TextField(blank=True)
    creation_date = models.DateTimeField(null=True, blank=True)
    modification_date = models.DateTimeField(null=True, blank=True)
    page_count = models.IntegerField(null=True, blank=True)
    word_count = models.IntegerField(null=True, blank=True)
    character_count = models.IntegerField(null=True, blank=True)
    
    class Meta:
        db_table = 'document_metadata'