# ML Service for Lost & Found

Python FastAPI microservice providing ML capabilities:
- Image captioning (BLIP)
- Text embeddings (sentence-transformers)
- Semantic search

## Setup

```bash
pip install -r requirements.txt
python main.py
```

Service runs on http://localhost:8000

## Endpoints

- POST /caption - Generate image description
- POST /embedding - Generate text embedding
- POST /embeddings/batch - Generate multiple embeddings
- POST /search - Semantic search
