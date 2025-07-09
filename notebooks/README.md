# IntelliDocs Jupyter Notebooks

This directory contains comprehensive Jupyter notebooks that demonstrate the IntelliDocs RAG system implementation.

## 📚 Available Notebooks

### 1. `intellidocs-rag-implementation.ipynb`

A comprehensive notebook that follows the structure of the reference [simple-local-rag.ipynb](https://colab.research.google.com/github/debarghya18/local-RAG/blob/main/simple-local-rag.ipynb) while showcasing the complete IntelliDocs system.

**Contents:**
- Setup and Environment Configuration
- Document Processing Pipeline
- Embedding Generation with Sentence Transformers
- Vector Storage and Similarity Search
- Complete RAG Pipeline Implementation
- Query Processing and Response Generation
- Performance Analysis and Visualizations
- Interactive Demo Interface
- Production Deployment Preparation

## 🚀 Getting Started

### Prerequisites

1. **Python Environment**: Ensure you have Python 3.11+ installed
2. **Dependencies**: Install required packages:
   ```bash
   pip install -r requirements_local.txt
   pip install jupyter matplotlib seaborn plotly
   ```

3. **Django Setup**: The notebook automatically configures Django environment

### Running the Notebook

1. **Start Jupyter**:
   ```bash
   jupyter notebook notebooks/
   ```

2. **Open the notebook**: Click on `intellidocs-rag-implementation.ipynb`

3. **Run all cells**: Execute cells sequentially or use "Run All"

### Alternative: Google Colab

You can also run this notebook in Google Colab:

1. Upload the notebook file to Google Colab
2. Install dependencies in the first cell:
   ```python
   !pip install django djangorestframework sentence-transformers PyPDF2 python-docx plotly
   ```
3. Upload the IntelliDocs project files or clone from repository

## 📊 What You'll Learn

### Core Concepts Demonstrated

1. **Document Processing**:
   - Text extraction from multiple formats (PDF, DOCX, TXT)
   - Intelligent chunking with overlap
   - Metadata extraction using spaCy NLP

2. **Embedding Generation**:
   - Sentence-BERT embeddings (all-MiniLM-L6-v2)
   - Batch processing for efficiency
   - Vector storage and indexing

3. **Similarity Search**:
   - Cosine similarity calculations
   - Top-K retrieval with thresholds
   - Performance optimization techniques

4. **RAG Pipeline**:
   - Query processing workflow
   - Context retrieval and ranking
   - Response generation with source attribution

5. **Production Features**:
   - User authentication and sessions
   - Database integration with Django ORM
   - Error handling and validation
   - Performance monitoring and health checks

### Visualizations Included

- Document processing statistics
- Embedding distribution analysis
- Similarity search performance metrics
- Query processing time trends
- System capacity and utilization charts

## 🔧 Customization

### Modifying Parameters

You can customize various aspects of the system:

```python
# Embedding model
embedding_generator = EmbeddingGenerator('all-MiniLM-L6-v2')

# Chunking parameters
chunks = processor._create_chunks(
    text=content,
    document=document,
    chunk_size=500,    # Adjust chunk size
    overlap=100        # Adjust overlap
)

# RAG configuration
config.top_k = 10                    # Number of results
config.similarity_threshold = 0.5    # Minimum similarity
config.temperature = 0.7             # Response creativity
```

### Adding New Documents

```python
# Add your own documents
sample_documents["Your_Document"] = """
Your document content here...
"""
```

### Custom Queries

```python
# Test with your own queries
custom_queries = [
    "Your question here?",
    "Another question?",
]
```

## 📈 Performance Benchmarks

The notebook includes comprehensive performance analysis:

- **Processing Speed**: ~100+ embeddings/second
- **Query Response**: <3 seconds average
- **Memory Usage**: ~1MB per 1000 embeddings
- **Accuracy**: >0.3 average similarity scores

## 🐛 Troubleshooting

### Common Issues

1. **Django Setup Errors**:
   ```python
   # Ensure Django is properly configured
   import os
   os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'intellidocs.settings_local')
   import django
   django.setup()
   ```

2. **Missing Dependencies**:
   ```bash
   pip install sentence-transformers spacy
   python -m spacy download en_core_web_sm
   ```

3. **Memory Issues**:
   - Reduce batch sizes for embedding generation
   - Use smaller chunk sizes for large documents
   - Clear variables between sections: `del large_variable`

4. **Database Issues**:
   - The notebook uses SQLite by default
   - Database is created automatically
   - Reset with: `rm db.sqlite3` and restart

### Getting Help

- Check the notebook's markdown cells for detailed explanations
- Review the IntelliDocs documentation in the main README
- Examine the source code in the respective modules
- Run individual cells to isolate issues

## 🎯 Next Steps

After completing the notebook:

1. **Deploy the System**:
   ```bash
   python run_local.py
   ```

2. **Access Web Interface**: http://localhost:8501

3. **Explore API**: http://localhost:8000/api/

4. **Scale for Production**: Consider Docker deployment

5. **Extend Functionality**: Add new document types, embedding models, or response generators

## 📝 Notes

- The notebook is designed to be self-contained and educational
- All code follows the production IntelliDocs architecture
- Performance metrics are based on the test environment
- Results may vary based on hardware and document content

---

**Happy Learning!** 🚀📚

This notebook provides a comprehensive introduction to building production-ready RAG systems with modern Python tools and frameworks.