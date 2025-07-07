import os
import logging
import json
import pickle
import numpy as np
from typing import List, Dict, Any, Optional
import fitz  # PyMuPDF
from sentence_transformers import SentenceTransformer
from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
import torch
from sklearn.metrics.pairwise import cosine_similarity
from tqdm import tqdm
import re

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
            # Detect device
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
            logger.info(f"Using device: {self.device}")
            
            # Load embedding model (lighter model for faster loading)
            logger.info("Loading embedding model...")
            self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
            
            # Load language model (using a smaller model for local deployment)
            logger.info("Loading language model...")
            model_name = "microsoft/DialoGPT-medium"  # Smaller model for local use
            
            try:
                self.llm_tokenizer = AutoTokenizer.from_pretrained(model_name)
                self.llm_model = AutoModelForCausalLM.from_pretrained(
                    model_name,
                    torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
                    device_map="auto" if self.device == "cuda" else None
                )
                
                # Add padding token if not present
                if self.llm_tokenizer.pad_token is None:
                    self.llm_tokenizer.pad_token = self.llm_tokenizer.eos_token
                
            except Exception as e:
                logger.warning(f"Failed to load DialoGPT, falling back to GPT-2: {e}")
                # Fallback to GPT-2
                model_name = "gpt2"
                self.llm_tokenizer = AutoTokenizer.from_pretrained(model_name)
                self.llm_model = AutoModelForCausalLM.from_pretrained(
                    model_name,
                    torch_dtype=torch.float16 if self.device == "cuda" else torch.float32
                )
                if self.llm_tokenizer.pad_token is None:
                    self.llm_tokenizer.pad_token = self.llm_tokenizer.eos_token
            
            self.models_loaded = True
            logger.info("Models loaded successfully!")
            
        except Exception as e:
            logger.error(f"Error loading models: {str(e)}")
            self.models_loaded = False
    
    def get_models_status(self) -> Dict[str, Any]:
        """Get status of loaded models."""
        return {
            "models_loaded": self.models_loaded,
            "device": self.device,
            "embedding_model": "all-MiniLM-L6-v2" if self.embedding_model else None,
            "llm_model": "DialoGPT-medium or GPT-2" if self.llm_model else None,
            "gpu_available": torch.cuda.is_available()
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
            doc = fitz.open(pdf_path)
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
            return pages_and_texts
            
        except Exception as e:
            logger.error(f"Error reading PDF: {str(e)}")
            return []
    
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
    
    def create_embeddings(self, chunks: List[Dict]) -> np.ndarray:
        """Create embeddings for text chunks."""
        if not self.embedding_model:
            raise ValueError("Embedding model not loaded")
        
        texts = [chunk["text"] for chunk in chunks]
        
        logger.info(f"Creating embeddings for {len(texts)} chunks...")
        embeddings = self.embedding_model.encode(
            texts,
            batch_size=32,
            show_progress_bar=True,
            convert_to_numpy=True
        )
        
        return embeddings
    
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
            
            # Create query embedding
            query_embedding = self.embedding_model.encode([query], convert_to_numpy=True)
            
            # Calculate similarities
            similarities = cosine_similarity(query_embedding, embeddings)[0]
            
            # Get top k most similar chunks
            top_indices = np.argsort(similarities)[-top_k:][::-1]
            
            relevant_chunks = []
            for idx in top_indices:
                chunk = chunks[idx].copy()
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
            
            # Generate response
            try:
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
                    response = f"Based on the document content, I found information related to your question on page(s) {', '.join(set(str(chunk['page_number']) for chunk in relevant_chunks))}. The relevant context suggests: {relevant_chunks[0]['text'][:200]}..."
                
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
                logger.error(f"Error generating response: {str(e)}")
                # Fallback to context-based response
                response = f"Based on the document, here's what I found: {relevant_chunks[0]['text'][:300]}..."
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
            logger.error(f"Error in generate_response: {str(e)}")
            return {"success": False, "error": str(e)}
