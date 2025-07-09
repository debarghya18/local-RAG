import logging
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from documents.models import Document
from documents.processors import DocumentValidator
from documents.tasks import process_document_task
from rag.models import RAGSession, RAGQuery
from rag.pipelines import RAGPipeline, RAGService
from .serializers import (
    DocumentSerializer, RAGSessionSerializer, RAGQuerySerializer,
    DocumentUploadSerializer
)
import datetime
from django.utils import timezone

logger = logging.getLogger(__name__)
User = get_user_model()

class DocumentViewSet(viewsets.ModelViewSet):
    serializer_class = DocumentSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Document.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    @action(detail=True, methods=['post'])
    def reprocess(self, request, pk=None):
        """Reprocess a document"""
        document = self.get_object()
        if document.processing_status == 'processing':
            return Response(
                {'error': 'Document is already being processed'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        document.processing_status = 'pending'
        document.save()
        
        # Queue processing task
        process_document_task.delay(str(document.id))
        
        return Response({'message': 'Document reprocessing started'})
    
    @action(detail=True, methods=['get'])
    def chunks(self, request, pk=None):
        """Get document chunks"""
        document = self.get_object()
        chunks = document.chunks.all()
        
        # Implement pagination
        page = self.paginate_queryset(chunks)
        if page is not None:
            serializer = DocumentChunkSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = DocumentChunkSerializer(chunks, many=True)
        return Response(serializer.data)

class RAGSessionViewSet(viewsets.ModelViewSet):
    serializer_class = RAGSessionSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return RAGSession.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    @action(detail=True, methods=['get'])
    def queries(self, request, pk=None):
        """Get session queries"""
        session = self.get_object()
        queries = session.queries.all()
        
        page = self.paginate_queryset(queries)
        if page is not None:
            serializer = RAGQuerySerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = RAGQuerySerializer(queries, many=True)
        return Response(serializer.data)

class DocumentUploadView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        serializer = DocumentUploadSerializer(data=request.data)
        if serializer.is_valid():
            file = serializer.validated_data['file']
            title = serializer.validated_data['title']
            description = serializer.validated_data.get('description', '')
            
            # Validate file
            validation_result = DocumentValidator.validate_file(file)
            if not validation_result['is_valid']:
                return Response(
                    {'errors': validation_result['errors']},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Create document
            document = Document.objects.create(
                user=request.user,
                title=title,
                description=description,
                file=file,
                file_type=validation_result['file_type'],
                file_size=validation_result['file_size']
            )
            
            # Queue processing
            process_document_task.delay(str(document.id))
            
            return Response(
                DocumentSerializer(document).data,
                status=status.HTTP_201_CREATED
            )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class RAGQueryView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        session_id = request.data.get('session_id')
        query_text = request.data.get('query_text')
        
        if not session_id or not query_text:
            return Response(
                {'error': 'session_id and query_text are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get session
        session = RAGService.get_session_by_id(session_id, request.user)
        if not session:
            return Response(
                {'error': 'Session not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        try:
            # Process query
            pipeline = RAGPipeline(request.user)
            query = pipeline.process_query(session, query_text)
            
            return Response(RAGQuerySerializer(query).data)
        except Exception as e:
            logger.error(f"Error processing RAG query: {str(e)}")
            return Response(
                {'error': 'Error processing query'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class HealthCheckView(APIView):
    permission_classes = []
    
    def get(self, request):
        return Response({
            'status': 'healthy',
            'timestamp': timezone.now().isoformat(),
            'version': '1.0.0'
        })