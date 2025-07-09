from rest_framework import serializers
from django.contrib.auth import get_user_model
from documents.models import Document, DocumentChunk
from rag.models import RAGSession, RAGQuery, RAGConfiguration

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'is_premium', 'created_at']
        read_only_fields = ['id', 'created_at']

class DocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = [
            'id', 'title', 'description', 'file', 'file_type', 'file_size',
            'processing_status', 'processed_at', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'processing_status', 'processed_at', 'created_at', 'updated_at']

class DocumentChunkSerializer(serializers.ModelSerializer):
    class Meta:
        model = DocumentChunk
        fields = ['id', 'chunk_index', 'content', 'metadata', 'created_at']
        read_only_fields = ['id', 'created_at']

class RAGSessionSerializer(serializers.ModelSerializer):
    documents = DocumentSerializer(many=True, read_only=True)
    document_ids = serializers.ListField(
        child=serializers.UUIDField(), write_only=True, required=False
    )
    
    class Meta:
        model = RAGSession
        fields = ['id', 'title', 'documents', 'document_ids', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def create(self, validated_data):
        document_ids = validated_data.pop('document_ids', [])
        session = RAGSession.objects.create(**validated_data)
        
        if document_ids:
            documents = Document.objects.filter(
                id__in=document_ids,
                user=self.context['request'].user
            )
            session.documents.set(documents)
        
        return session

class RAGQuerySerializer(serializers.ModelSerializer):
    class Meta:
        model = RAGQuery
        fields = [
            'id', 'query_text', 'response_text', 'sources', 'metadata',
            'processing_time', 'created_at'
        ]
        read_only_fields = ['id', 'response_text', 'sources', 'metadata', 'processing_time', 'created_at']

class RAGConfigurationSerializer(serializers.ModelSerializer):
    class Meta:
        model = RAGConfiguration
        fields = [
            'model_name', 'chunk_size', 'chunk_overlap', 'max_tokens',
            'temperature', 'top_k', 'similarity_threshold', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

class DocumentUploadSerializer(serializers.Serializer):
    file = serializers.FileField()
    title = serializers.CharField(max_length=255)
    description = serializers.CharField(required=False, allow_blank=True)
    
    def validate_file(self, value):
        # File validation is handled by DocumentValidator
        return value