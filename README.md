# 🕉️ SvaramAI - Sanskrit Intelligence Suite

**Production-grade FastAPI backend for Sanskrit language AI processing with RAG, semantic search, and multi-LLM support**

[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-green.svg)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

---

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Installation](#installation)
- [Configuration](#configuration)
- [Running the API](#running-the-api)
- [API Endpoints](#api-endpoints)
- [Usage Examples](#usage-examples)
- [Development](#development)
- [Testing](#testing)
- [Deployment](#deployment)
- [License](#license)

---

## 🌟 Overview

SvaramAI is a comprehensive AI-powered backend system for Sanskrit language processing. It combines modern AI/ML technologies (Groq, local embeddings, Qdrant vector database) with traditional Sanskrit scholarship to provide:

- **Chandas Identification**: Analyze prosody and identify Sanskrit meters with Groq LLM + algorithmic fallback
- **Shloka Generation**: Create authentic Sanskrit verses using Groq AI
- **Branding Taglines**: Generate Sanskrit taglines for modern businesses
- **Meaning Extraction**: Translate and analyze Sanskrit texts
- **Knowledge Base**: RAG-powered semantic search with Qdrant and local embeddings
- **PDF Upload**: Extract, chunk, and embed Sanskrit PDFs for semantic search
- **Voice Analysis**: (Future) Pronunciation accuracy assessment

---

## ✨ Features

### 🔍 1. Chandas Identifier - Prosody AI Engine
- **Groq LLM Integration** with llama-3.3-70b-versatile
- Syllable-by-syllable breakdown with Laghu/Guru classification
- Meter identification with confidence scores
- **Algorithmic Fallback** when LLM unavailable
- Support for major Sanskrit meters (Anushtup, Indravajra, Upajati, etc.)
- Handles partial verses and incomplete shlokas

### ✍️ 2. Shloka Generator - AI Shloka Composer
- Theme-based verse generation
- Multiple moods (devotional, philosophical, heroic)
- Various styles (classical, Vedic, Puranic, modern)
- Meter-specific composition
- English translations included

### 🎯 3. Sanskrit Tagline Generator
- Corporate branding in Sanskrit
- Industry-specific vocabulary
- Multiple tone options
- Alternative variants
- Cultural authenticity

### 📖 4. Meaning Engine - Translation & Analysis
- Complete English translations
- Word-by-word breakdowns
- Historical and cultural context
- Grammatical analysis
- Source identification

### 🗄️ 5. RAG Knowledge Base
- **Qdrant vector database** integration (localhost:6333)
- **Local embeddings** with sentence-transformers (paraphrase-multilingual-MiniLM-L12-v2)
- 384-dimensional vectors for semantic search
- **PDF Upload & Processing** with automatic chunking (1000 chars, 100 overlap)
- Multiple specialized collections (chandas_patterns, example_shlokas, grammar_rules, branding_vocab)
- CRUD operations for documents
- Semantic search with ranked results
- Context retrieval for AI modules
- Auto-recreation of collections on vector dimension mismatch

### 🎤 6. Voice Karaoke Analyzer (Future)
- Speech-to-text for Sanskrit
- Pronunciation accuracy scoring
- Error detection and suggestions
- Real-time feedback

---

## 🏗️ Architecture

### Clean Architecture Pattern

```
┌─────────────────────────────────────────┐
│           FastAPI Routes                │
│  (API Layer - HTTP Endpoints)           │
└───────────────┬─────────────────────────┘
                │
┌───────────────▼─────────────────────────┐
│          Controllers                    │
│  (Business Logic Layer)                 │
└───────────────┬─────────────────────────┘
                │
┌───────────────▼─────────────────────────┐
│           Services                      │
│  (LLM, RAG, PDF Processing)             │
└───────────────┬─────────────────────────┘
                │
┌───────────────▼─────────────────────────┐
│      External Services                  │
│  (OpenAI, Anthropic, Qdrant)           │
└─────────────────────────────────────────┘
```

### Directory Structure

```
backend/
├── main.py                    # FastAPI application entry point
├── config.py                  # Configuration management
├── models.py                  # Pydantic request/response models
├── requirements.txt           # Python dependencies
├── .env.example              # Environment variables template
│
├── routes/                   # API route definitions
│   ├── chandas_routes.py
│   ├── shloka_routes.py
│   ├── tagline_routes.py
│   ├── meaning_routes.py
│   └── knowledgebase_routes.py
│
├── controllers/              # Business logic layer
│   ├── chandas_controller.py
│   ├── shloka_controller.py
│   ├── tagline_controller.py
│   ├── meaning_controller.py
│   └── knowledgebase_controller.py
│
├── services/                 # External service clients
│   ├── llm_client.py         # OpenAI/Anthropic wrapper
│   ├── rag_client.py         # Qdrant vector DB client
│   └── pdf_loader.py         # PDF processing
│
├── prompts/                  # System prompts for LLMs
│   ├── chandas_system.txt
│   ├── shloka_generate.txt
│   ├── tagline_system.txt
│   └── meaning_system.txt
│
└── utils/                    # Utility functions
    ├── text_cleaner.py       # Sanskrit text processing
    ├── splitter.py           # Syllable splitting
    └── helpers.py            # General utilities
```

---

## 📦 Installation

### Prerequisites

- **Python 3.11+** (Tested on Python 3.12.1)
- **Qdrant** (Vector database for RAG)
- **Groq API Key** (Primary LLM provider)
- **Optional**: OpenAI or Anthropic API keys for additional LLM providers

### Step 1: Clone Repository

```bash
cd c:\Projects\Chanda\backend
```

### Step 2: Create Virtual Environment

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### Step 3: Install Dependencies

```powershell
pip install -r requirements.txt
```

### Step 4: Install Qdrant (Local)

**Using Docker:**
```powershell
docker pull qdrant/qdrant
docker run -p 6333:6333 qdrant/qdrant
```

**Or download from:** https://qdrant.tech/documentation/quick-start/

---

## ⚙️ Configuration

### Environment Variables

1. Copy the example environment file:
```powershell
Copy-Item .env.example .env
```

2. Edit `.env` with your configuration:

```env
# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=True

# API Keys
GROQ_API_KEY=gsk_your-groq-key-here
OPENAI_API_KEY=sk-your-openai-key-here  # Optional
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key-here  # Optional

# LLM Configuration
DEFAULT_LLM_PROVIDER=groq
GROQ_MODEL=llama-3.3-70b-versatile
OPENAI_MODEL=gpt-4-turbo-preview
ANTHROPIC_MODEL=claude-3-opus-20240229
LLM_TEMPERATURE=0.7
LLM_MAX_TOKENS=2000

# Qdrant Configuration
QDRANT_HOST=localhost
QDRANT_PORT=6333
QDRANT_API_KEY=
QDRANT_USE_HTTPS=False

# Collection Names
CHANDAS_COLLECTION=chandas_patterns
SHLOKAS_COLLECTION=example_shlokas
GRAMMAR_COLLECTION=grammar_rules
BRANDING_COLLECTION=branding_vocab

# Embedding Configuration
EMBEDDING_MODEL=paraphrase-multilingual-MiniLM-L12-v2
VECTOR_SIZE=384
```

### Required API Keys

- **Groq**: Get from https://console.groq.com/keys (Primary LLM provider)
- **OpenAI** (Optional): Get from https://platform.openai.com/api-keys
- **Anthropic** (Optional): Get from https://console.anthropic.com/

---

## 🚀 Running the API

### Development Mode

```powershell
python main.py
```

Or with uvicorn directly:
```powershell
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Production Mode

```powershell
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Access the API

- **API**: http://localhost:8000
- **Interactive Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

## 📡 API Endpoints

### Health Check
- `GET /` - Root endpoint
- `GET /health` - Health check with service status

### Chandas Identifier
- `POST /api/v1/chandas/identify` - Identify meter from shloka

### Shloka Generator
- `POST /api/v1/shloka/generate` - Generate Sanskrit verse

### Tagline Generator
- `POST /api/v1/tagline/generate` - Generate Sanskrit taglines

### Meaning Engine
- `POST /api/v1/meaning/extract` - Extract meaning and translation

### Knowledge Base
- `POST /api/v1/kb/document` - Add document to collection
- `POST /api/v1/kb/search` - Semantic search across documents
- `POST /api/v1/kb/upload-pdf` - Upload and process PDF file
- `PUT /api/v1/kb/document` - Update existing document
- `DELETE /api/v1/kb/document` - Delete document by ID
- `GET /api/v1/kb/collection/{collection}/stats` - Get collection statistics

---

## 💡 Usage Examples

### 1. Identify Chandas

```powershell
$body = @{
    shloka = "वसुदेवसुतं देवं कंसचाणूरमर्दनम्"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/api/v1/chandas/identify" `
    -Method Post `
    -Body $body `
    -ContentType "application/json"
```

**Response:**
```json
{
  "chandas_name": "Anushtup",
  "syllable_breakdown": [
    {"syllable": "va", "type": "laghu", "position": 1},
    {"syllable": "su", "type": "laghu", "position": 2}
  ],
  "laghu_guru_pattern": "LGGLGGLG",
  "explanation": "This is Anushtup meter with 8 syllables per quarter",
  "confidence": 0.95
}
```

### 2. Generate Shloka

```powershell
$body = @{
    theme = "Krishna's divine play"
    deity = "Krishna"
    mood = "devotional"
    style = "classical"
    meter = "Anushtup"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/api/v1/shloka/generate" `
    -Method Post `
    -Body $body `
    -ContentType "application/json"
```

### 3. Generate Tagline

```powershell
$body = @{
    industry = "Technology"
    company_name = "TechVeda"
    vision = "Empowering digital transformation"
    values = @("innovation", "excellence", "integrity")
    tone = "professional"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/api/v1/tagline/generate" `
    -Method Post `
    -Body $body `
    -ContentType "application/json"
```

### 4. Extract Meaning

```powershell
$body = @{
    verse = "सत्यं ज्ञानमनन्तं ब्रह्म"
    include_word_meanings = $true
    include_context = $true
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/api/v1/meaning/extract" `
    -Method Post `
    -Body $body `
    -ContentType "application/json"
```

### 5. Add to Knowledge Base

```powershell
$body = @{
    collection = "chandas_patterns"
    content = "Anushtup: 8 syllables per quarter, 32 total"
    metadata = @{
        name = "Anushtup"
        category = "sama-vritta"
        syllables = 32
    }
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/api/v1/kb/document" `
    -Method Post `
    -Body $body `
    -ContentType "application/json"
```

### 6. Upload PDF to Knowledge Base

```powershell
# Using multipart/form-data
$pdfPath = "C:\path\to\sanskrit_text.pdf"
$collection = "chandas_patterns"

$form = @{
    file = Get-Item -Path $pdfPath
    collection = $collection
}

Invoke-RestMethod -Uri "http://localhost:8000/api/v1/kb/upload-pdf" `
    -Method Post `
    -Form $form
```

**Response:**
```json
{
  "message": "PDF processed successfully",
  "chunks_added": 127,
  "collection": "chandas_patterns",
  "filename": "sanskrit_text.pdf"
}
```

### 7. Semantic Search in Knowledge Base

```powershell
$body = @{
    query = "What is Anushtup meter?"
    collection = "chandas_patterns"
    limit = 5
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/api/v1/kb/search" `
    -Method Post `
    -Body $body `
    -ContentType "application/json"
```

**Response:**
```json
{
  "results": [
    {
      "content": "Anushtup is the most common Sanskrit meter...",
      "score": 0.87,
      "metadata": {
        "page_number": 1,
        "chunk_id": 0,
        "source_file": "sanskrit_text.pdf"
      }
    }
  ]
}
```

---

## 🛠️ Development

### Code Style

The project follows:
- **PEP 8** style guide
- **Type hints** for all functions
- **Docstrings** for all modules, classes, and functions
- **Async/await** for I/O operations

### Adding a New Module

1. Create model in `models.py`
2. Create controller in `controllers/`
3. Create routes in `routes/`
4. Create system prompt in `prompts/`
5. Update `main.py` to include router

### Logging

All modules use Python's `logging` module:
```python
import logging
logger = logging.getLogger(__name__)
logger.info("Message")
```

---

## 🧪 Testing

### Run Tests

```powershell
pytest tests/ -v
```

### Test Coverage

```powershell
pytest --cov=. --cov-report=html
```

### Manual API Testing

Use the interactive docs at `http://localhost:8000/docs`

---

## 🚢 Deployment

### Using Docker

Create `Dockerfile`:
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Build and run:
```powershell
docker build -t sanskrit-ai .
docker run -p 8000:8000 --env-file .env sanskrit-ai
```

### Production Checklist

- [ ] Set `DEBUG=False` in `.env`
- [ ] Use production-grade ASGI server (uvicorn with workers)
- [ ] Set up reverse proxy (nginx)
- [ ] Enable HTTPS
- [ ] Configure CORS properly
- [ ] Set up monitoring and logging
- [ ] Use secret management for API keys
- [ ] Set up database backups (Qdrant)

---

## 📚 Documentation

- **API Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Source Code**: Fully documented with docstrings

---

## 🤝 Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

---

## 📄 License

This project is licensed under the MIT License.

---

## 🙏 Acknowledgments

- **FastAPI**: Modern async web framework
- **Groq**: Fast LLM inference with llama-3.3-70b-versatile
- **Qdrant**: High-performance vector database
- **sentence-transformers**: Local multilingual embeddings
- **Sanskrit Scholars**: Traditional knowledge preservation

---

## 🔧 Technical Stack

- **Backend**: FastAPI 0.109+ with Uvicorn
- **LLM**: Groq (llama-3.3-70b-versatile) with fallback to OpenAI/Anthropic
- **Embeddings**: sentence-transformers (paraphrase-multilingual-MiniLM-L12-v2) - 384-dim vectors
- **Vector DB**: Qdrant 1.7.3+ on localhost:6333
- **PDF Processing**: PyPDF2 with chunking strategy
- **Python**: 3.11+ (tested on 3.12.1)
- **Architecture**: Clean Routes → Controllers → Services pattern

---

## 📧 Support

For issues and questions:
- Open an issue on GitHub
- Check the documentation at `/docs`

---

**Built with ❤️ for Sanskrit AI Processing by the SvaramAI Team**

*Preserving ancient wisdom with modern technology* 🕉️
