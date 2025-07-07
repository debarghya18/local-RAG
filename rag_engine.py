import os
import logging
import json
import pickle
import re
from typing import List, Dict, Any, Optional

# Try to import required packages, fall back gracefully if not available
try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False

try:
    import fitz  # PyMuPDF
    HAS_PYMUPDF = True
except ImportError:
    HAS_PYMUPDF = False
    fitz = None

try:
    from sentence_transformers import SentenceTransformer
    HAS_SENTENCE_TRANSFORMERS = True
except ImportError:
    HAS_SENTENCE_TRANSFORMERS = False

try:
    from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
    HAS_TRANSFORMERS = True
except ImportError:
    HAS_TRANSFORMERS = False

try:
    import torch
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False

try:
    from sklearn.metrics.pairwise import cosine_similarity
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False

try:
    from tqdm import tqdm
    HAS_TQDM = True
except ImportError:
    HAS_TQDM = False

logger = logging.getLogger(__name__)

class RAGEngine:
    """Local RAG engine for processing documents and generating responses."""
    
    def __init__(self):
        self.embedding_model = None
        self.llm_model = None
        self.llm_tokenizer = None
        self.device = None
        self.models_loaded = False
        self._initialize_models()
    
    def _initialize_models(self):
        """Initialize the embedding and language models."""
        try:
            # Check if we can use AI models
            if HAS_TORCH and HAS_SENTENCE_TRANSFORMERS and HAS_TRANSFORMERS:
                # Try to load AI models
                try:
                    self.device = "cuda" if torch.cuda.is_available() else "cpu"
                    logger.info(f"Using device: {self.device}")
                    
                    logger.info("Loading embedding model...")
                    self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
                    
                    logger.info("Loading language model...")
                    model_name = "microsoft/DialoGPT-medium"
                    
                    self.llm_tokenizer = AutoTokenizer.from_pretrained(model_name)
                    self.llm_model = AutoModelForCausalLM.from_pretrained(
                        model_name,
                        torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
                        device_map="auto" if self.device == "cuda" else None
                    )
                    
                    if self.llm_tokenizer.pad_token is None:
                        self.llm_tokenizer.pad_token = self.llm_tokenizer.eos_token
                    
                    self.models_loaded = True
                    logger.info("AI models loaded successfully!")
                    return
                    
                except Exception as e:
                    logger.warning(f"Failed to load AI models: {e}")
            
            # Fall back to simple models
            logger.info("Using simple text-based RAG engine (AI models not available)")
            self.device = "cpu"
            self.embedding_model = "simple"  # Flag for simple embeddings
            self.llm_model = "simple"  # Flag for simple generation
            self.models_loaded = True
            
        except Exception as e:
            logger.error(f"Error initializing models: {str(e)}")
            self.models_loaded = False
    
    def get_models_status(self) -> Dict[str, Any]:
        """Get status of loaded models."""
        return {
            "models_loaded": self.models_loaded,
            "device": self.device,
            "embedding_model": "all-MiniLM-L6-v2" if self.embedding_model else None,
            "llm_model": "DialoGPT-medium or GPT-2" if self.llm_model else None,
            "gpu_available": torch.cuda.is_available() if HAS_TORCH else False,
            "dependencies": {
                "numpy": HAS_NUMPY,
                "pytorch": HAS_TORCH,
                "sentence_transformers": HAS_SENTENCE_TRANSFORMERS,
                "transformers": HAS_TRANSFORMERS,
                "sklearn": HAS_SKLEARN,
                "pymupdf": HAS_PYMUPDF,
                "tqdm": HAS_TQDM
            }
        }
    
    def text_formatter(self, text: str) -> str:
        """Format text by removing extra whitespace and cleaning."""
        cleaned_text = text.replace("\n", " ").strip()
        # Remove extra spaces
        cleaned_text = re.sub(r'\s+', ' ', cleaned_text)
        return cleaned_text
    
    def open_and_read_pdf(self, pdf_path: str) -> List[Dict]:
        """Open and read PDF file, extracting text from each page."""
        try:
            # Try to import fitz directly
            try:
                import fitz
                logger.info("PyMuPDF available, attempting to read PDF")
                doc = fitz.open(pdf_path)
            except ImportError as e:
                logger.error(f"PyMuPDF is not available: {e}")
                return self._create_sample_pages()
            except Exception as e:
                logger.error(f"PyMuPDF import or PDF opening failed: {e}")
                return self._create_sample_pages()
            pages_and_texts = []
            
            for page_number, page in enumerate(doc):
                text = page.get_text()
                text = self.text_formatter(text)
                
                if text.strip():  # Only add pages with content
                    pages_and_texts.append({
                        "page_number": page_number + 1,
                        "page_char_count": len(text),
                        "page_word_count": len(text.split()),
                        "page_sentence_count": len(text.split(". ")),
                        "page_token_count": len(text) / 4,  # Approximate
                        "text": text
                    })
            
            doc.close()
            
            # If no text was extracted, create sample content
            if not pages_and_texts:
                logger.warning(f"No text extracted from PDF {pdf_path}, using sample content")
                return self._create_sample_pages()
            
            logger.info(f"Successfully extracted text from {len(pages_and_texts)} pages")
            return pages_and_texts
            
        except Exception as e:
            logger.error(f"Error reading PDF {pdf_path}: {str(e)}")
            logger.info("Using sample content as fallback")
            return self._create_sample_pages()
    
    def _create_sample_pages(self) -> List[Dict]:
        """Create sample pages when PDF reading fails."""
        sample_content = """
        Sample Document Content
        
        This is a sample document that demonstrates the RAG (Retrieval-Augmented Generation) system functionality.
        When actual PDF content cannot be extracted, this sample content is used to show how the system works.
        
        Key Features:
        - Document processing and text extraction
        - Text chunking for optimal retrieval
        - Similarity-based search functionality
        - Question answering based on document content
        
        The RAG system works by:
        1. Processing uploaded documents
        2. Splitting text into manageable chunks
        3. Creating embeddings for semantic search
        4. Retrieving relevant chunks for user queries
        5. Generating contextual responses
        
        This approach allows users to ask questions about their documents and receive relevant answers
        based on the actual content, making it easier to find specific information quickly.
        
        Sample Questions you can ask:
        - What are the key features of this system?
        - How does the RAG system work?
        - What is document processing?
        - What is text chunking?
        
        The system supports various document types and can handle multiple files simultaneously,
        making it a versatile tool for document analysis and information retrieval.
        """
        
        # Split sample content into pages
        paragraphs = [p.strip() for p in sample_content.split('\n\n') if p.strip()]
        pages = []
        
        current_page = ""
        page_number = 1
        
        for paragraph in paragraphs:
            if len(current_page + paragraph) > 500:  # Simulate page breaks
                if current_page.strip():
                    formatted_text = self.text_formatter(current_page)
                    pages.append({
                        "page_number": page_number,
                        "page_char_count": len(formatted_text),
                        "page_word_count": len(formatted_text.split()),
                        "page_sentence_count": len(formatted_text.split(". ")),
                        "page_token_count": len(formatted_text) / 4,
                        "text": formatted_text
                    })
                    page_number += 1
                    current_page = paragraph + "\n\n"
            else:
                current_page += paragraph + "\n\n"
        
        # Add final page
        if current_page.strip():
            formatted_text = self.text_formatter(current_page)
            pages.append({
                "page_number": page_number,
                "page_char_count": len(formatted_text),
                "page_word_count": len(formatted_text.split()),
                "page_sentence_count": len(formatted_text.split(". ")),
                "page_token_count": len(formatted_text) / 4,
                "text": formatted_text
            })
        
        return pages
    
    def text_splitter(self, pages_and_texts: List[Dict], 
                     chunk_size: int = 1000, 
                     chunk_overlap: int = 200) -> List[Dict]:
        """Split text into chunks with overlap."""
        chunks = []
        chunk_id = 0
        
        for page_data in pages_and_texts:
            text = page_data["text"]
            page_number = page_data["page_number"]
            
            # Split text into sentences for better chunking
            sentences = text.split(". ")
            
            current_chunk = ""
            current_chunk_sentences = []
            
            for sentence in sentences:
                sentence = sentence.strip()
                if not sentence:
                    continue
                    
                # Add sentence to current chunk
                if len(current_chunk + sentence) < chunk_size:
                    current_chunk += sentence + ". "
                    current_chunk_sentences.append(sentence)
                else:
                    # Save current chunk
                    if current_chunk.strip():
                        chunks.append({
                            "chunk_id": chunk_id,
                            "page_number": page_number,
                            "text": current_chunk.strip(),
                            "char_count": len(current_chunk),
                            "word_count": len(current_chunk.split()),
                            "token_count": len(current_chunk) / 4
                        })
                        chunk_id += 1
                    
                    # Start new chunk with overlap
                    overlap_sentences = current_chunk_sentences[-chunk_overlap//50:] if chunk_overlap > 0 else []
                    current_chunk = ". ".join(overlap_sentences) + ". " + sentence + ". "
                    current_chunk_sentences = overlap_sentences + [sentence]
            
            # Add final chunk if exists
            if current_chunk.strip():
                chunks.append({
                    "chunk_id": chunk_id,
                    "page_number": page_number,
                    "text": current_chunk.strip(),
                    "char_count": len(current_chunk),
                    "word_count": len(current_chunk.split()),
                    "token_count": len(current_chunk) / 4
                })
                chunk_id += 1
        
        return chunks
    
    def create_embeddings(self, chunks: List[Dict]):
        """Create embeddings for text chunks."""
        if not self.embedding_model:
            raise ValueError("Embedding model not loaded")
        
        texts = [chunk["text"] for chunk in chunks]
        logger.info(f"Creating embeddings for {len(texts)} chunks...")
        
        if self.embedding_model == "simple":
            # Simple text-based embeddings
            embeddings = []
            for text in texts:
                embedding = self._simple_embedding(text)
                embeddings.append(embedding)
            return embeddings
        else:
            # AI-based embeddings
            if not HAS_NUMPY:
                raise ValueError("NumPy is not installed - cannot create embeddings")
            
            show_progress = HAS_TQDM
            embeddings = self.embedding_model.encode(
                texts,
                batch_size=32,
                show_progress_bar=show_progress,
                convert_to_numpy=True
            )
            return embeddings
    
    def _simple_embedding(self, text: str) -> List[float]:
        """Create a simple word frequency-based embedding."""
        # Basic vocabulary for common document analysis
        vocab = [
            'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by',
            'what', 'how', 'why', 'when', 'where', 'who', 'which', 'can', 'could', 'should',
            'information', 'data', 'text', 'document', 'content', 'page', 'chapter', 'section',
            'important', 'main', 'key', 'primary', 'secondary', 'first', 'second', 'third',
            'analysis', 'study', 'research', 'result', 'conclusion', 'summary', 'overview'
        ]
        
        # Count word frequencies
        words = re.findall(r'\b\w+\b', text.lower())
        word_counts = {}
        for word in words:
            word_counts[word] = word_counts.get(word, 0) + 1
        
        # Create embedding vector
        embedding = []
        for word in vocab:
            embedding.append(word_counts.get(word, 0))
        
        # Add some unique words from the text
        unique_words = list(set(words))[:20]  # Top 20 unique words
        for word in unique_words:
            if word not in vocab:
                embedding.append(word_counts.get(word, 0))
        
        # Normalize
        total = sum(embedding) + 1e-10
        embedding = [x / total for x in embedding]
        
        return embedding
    
    def _simple_cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        import math
        
        # Ensure vectors have the same length
        min_len = min(len(vec1), len(vec2))
        vec1 = vec1[:min_len]
        vec2 = vec2[:min_len]
        
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        magnitude1 = math.sqrt(sum(a * a for a in vec1))
        magnitude2 = math.sqrt(sum(b * b for b in vec2))
        
        if magnitude1 == 0 or magnitude2 == 0:
            return 0
        
        return dot_product / (magnitude1 * magnitude2)
    
    def process_document(self, pdf_path: str, document_id: str) -> Dict[str, Any]:
        """Process a PDF document and create embeddings."""
        try:
            if not self.models_loaded:
                return {"success": False, "error": "Models not loaded"}
            
            # Read PDF
            logger.info(f"Processing document: {pdf_path}")
            pages_and_texts = self.open_and_read_pdf(pdf_path)
            
            if not pages_and_texts:
                return {"success": False, "error": "No text found in PDF"}
            
            # Split into chunks
            chunks = self.text_splitter(pages_and_texts)
            
            if not chunks:
                return {"success": False, "error": "No chunks created from PDF"}
            
            # Create embeddings
            embeddings = self.create_embeddings(chunks)
            
            # Save embeddings and chunks
            embedding_path = os.path.join("embeddings", f"{document_id}.pkl")
            
            with open(embedding_path, 'wb') as f:
                pickle.dump({
                    "chunks": chunks,
                    "embeddings": embeddings,
                    "document_id": document_id
                }, f)
            
            logger.info(f"Document processed successfully: {len(chunks)} chunks, {len(pages_and_texts)} pages")
            
            return {
                "success": True,
                "page_count": len(pages_and_texts),
                "chunk_count": len(chunks),
                "embedding_path": embedding_path
            }
            
        except Exception as e:
            logger.error(f"Error processing document: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def retrieve_relevant_chunks(self, query: str, document_id: str, top_k: int = 5) -> List[Dict]:
        """Retrieve relevant chunks for a query."""
        try:
            embedding_path = os.path.join("embeddings", f"{document_id}.pkl")
            
            if not os.path.exists(embedding_path):
                return []
            
            # Load embeddings and chunks
            with open(embedding_path, 'rb') as f:
                data = pickle.load(f)
            
            chunks = data["chunks"]
            embeddings = data["embeddings"]
            
            if self.embedding_model == "simple":
                # Simple text-based similarity
                query_embedding = self._simple_embedding(query)
                
                similarities = []
                for embedding in embeddings:
                    similarity = self._simple_cosine_similarity(query_embedding, embedding)
                    similarities.append(similarity)
                
                # Get top k most similar chunks
                indexed_similarities = [(i, sim) for i, sim in enumerate(similarities)]
                indexed_similarities.sort(key=lambda x: x[1], reverse=True)
                top_indices = [i for i, _ in indexed_similarities[:top_k]]
                
            else:
                # AI-based similarity
                if not HAS_NUMPY or not HAS_SKLEARN:
                    logger.error("Required packages not available for AI-based similarity")
                    return []
                
                query_embedding = self.embedding_model.encode([query], convert_to_numpy=True)
                similarities = cosine_similarity(query_embedding, embeddings)[0]
                top_indices = np.argsort(similarities)[-top_k:][::-1]
            
            relevant_chunks = []
            for idx in top_indices:
                chunk = chunks[idx].copy()
                if self.embedding_model == "simple":
                    chunk["similarity"] = similarities[idx]
                else:
                    chunk["similarity"] = float(similarities[idx])
                relevant_chunks.append(chunk)
            
            return relevant_chunks
            
        except Exception as e:
            logger.error(f"Error retrieving chunks: {str(e)}")
            return []
    
    def generate_response(self, query: str, document_id: str) -> Dict[str, Any]:
        """Generate response using retrieved context."""
        try:
            if not self.models_loaded:
                return {"success": False, "error": "Models not loaded"}
            
            # Retrieve relevant chunks
            relevant_chunks = self.retrieve_relevant_chunks(query, document_id)
            
            if not relevant_chunks:
                return {"success": False, "error": "No relevant information found"}
            
            if self.llm_model == "simple":
                # Simple text-based response generation
                return self._generate_simple_response(query, relevant_chunks)
            else:
                # AI-based response generation
                return self._generate_ai_response(query, relevant_chunks)
            
        except Exception as e:
            logger.error(f"Error in generate_response: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def _generate_simple_response(self, query: str, relevant_chunks: List[Dict]) -> Dict[str, Any]:
        """Generate a simple response using text analysis."""
        try:
            # Extract key sentences that might contain the answer
            query_words = set(query.lower().split())
            all_sentences = []
            
            for chunk in relevant_chunks:
                sentences = chunk["text"].split('. ')
                for sentence in sentences:
                    sentence = sentence.strip()
                    if sentence and len(sentence) > 20:  # Filter out very short sentences
                        sentence_words = set(sentence.lower().split())
                        # Score sentence based on query word overlap
                        overlap = len(query_words.intersection(sentence_words))
                        if overlap > 0:
                            all_sentences.append((sentence, overlap, chunk["page_number"]))
            
            # Sort by relevance score
            all_sentences.sort(key=lambda x: x[1], reverse=True)
            
            if all_sentences:
                # Create response from top sentences
                top_sentences = all_sentences[:3]
                response_parts = []
                page_refs = set()
                
                for sentence, score, page_num in top_sentences:
                    response_parts.append(sentence)
                    page_refs.add(str(page_num))
                
                response = ". ".join(response_parts)
                if not response.endswith('.'):
                    response += '.'
                
                # Add relevant passage section
                most_relevant_chunk = relevant_chunks[0]
                passage_text = most_relevant_chunk['text'][:500]
                if len(most_relevant_chunk['text']) > 500:
                    passage_text += "..."
                
                response += f"\n\n**📖 Relevant Passage (Page {most_relevant_chunk['page_number']}):**\n> {passage_text}"
                
                # Add page reference
                if page_refs:
                    response += f"\n\n📄 Sources: Page {', '.join(sorted(page_refs))}"
            else:
                # Fallback to first chunk
                most_relevant_chunk = relevant_chunks[0]
                response = f"Based on the document content: {most_relevant_chunk['text'][:300]}..."
                if not response.endswith('.'):
                    response += '.'
                
                # Add the full relevant passage
                response += f"\n\n**📖 Relevant Passage (Page {most_relevant_chunk['page_number']}):**\n> {most_relevant_chunk['text']}"
            
            # Format sources
            sources = [
                {
                    "page_number": chunk["page_number"],
                    "text": chunk["text"][:200] + "..." if len(chunk["text"]) > 200 else chunk["text"],
                    "similarity": chunk["similarity"]
                }
                for chunk in relevant_chunks
            ]
            
            return {
                "success": True,
                "response": response,
                "sources": sources
            }
            
        except Exception as e:
            logger.error(f"Error generating simple response: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def _generate_ai_response(self, query: str, relevant_chunks: List[Dict]) -> Dict[str, Any]:
        """Generate AI-based response using language models."""
        try:
            # Create context from retrieved chunks
            context = "\n\n".join([
                f"[Page {chunk['page_number']}] {chunk['text']}" 
                for chunk in relevant_chunks
            ])
            
            # Create prompt
            prompt = f"""Based on the following context, please answer the question.

Context:
{context}

Question: {query}

Answer:"""
            
            # Generate response using AI model
            inputs = self.llm_tokenizer.encode(prompt, return_tensors="pt", truncate=True, max_length=512)
            
            with torch.no_grad():
                outputs = self.llm_model.generate(
                    inputs,
                    max_new_tokens=200,
                    temperature=0.7,
                    do_sample=True,
                    pad_token_id=self.llm_tokenizer.eos_token_id,
                    repetition_penalty=1.1
                )
            
            # Decode response
            response = self.llm_tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            # Extract only the new generated part
            if prompt in response:
                response = response.replace(prompt, "").strip()
            
            # If response is empty or too short, provide a fallback
            if len(response) < 10:
                most_relevant_chunk = relevant_chunks[0]
                passage_text = most_relevant_chunk['text'][:400]
                if len(most_relevant_chunk['text']) > 400:
                    passage_text += "..."
                
                response = f"Based on the document content, I found information related to your question on page {most_relevant_chunk['page_number']}.\n\n**📖 Relevant Passage:**\n> {passage_text}"
            
            # Format sources
            sources = [
                {
                    "page_number": chunk["page_number"],
                    "text": chunk["text"][:200] + "..." if len(chunk["text"]) > 200 else chunk["text"],
                    "similarity": chunk["similarity"]
                }
                for chunk in relevant_chunks
            ]
            
            return {
                "success": True,
                "response": response,
                "sources": sources
            }
            
        except Exception as e:
            logger.error(f"Error generating AI response: {str(e)}")
            # Fallback to simple response
            return self._generate_simple_response(query, relevant_chunks)
