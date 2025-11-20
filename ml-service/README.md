# ML Service for Lost & Found - Python 3.13 Compatible

**Completely refactored ML service that works with Python 3.13.5 without PyTorch or sentence-transformers.**

## What Changed?

### Old Stack (Incompatible with Python 3.13)
- PyTorch 2.1.0
- Transformers 4.35.0
- sentence-transformers 2.2.2
- BLIP model (local, GPU/CPU)

### New Stack (Python 3.13.5 Compatible)
- **scikit-learn** for TF-IDF text embeddings
- **Color-based image analysis** for basic captioning
- **Optional Hugging Face Inference API** for advanced image captioning
- **NumPy 2.2.1** (Python 3.13 compatible)
- **FastAPI 0.115.0** (latest)

## Features

### 1. Text Embeddings (TF-IDF)
- Generates 384-dimensional vectors (matching old sentence-transformers output)
- Uses TF-IDF with bigrams and English stop words
- Pre-trained on common lost & found item terms
- Normalized vectors for cosine similarity
- **No external dependencies or models needed**

### 2. Image Captioning (Two Modes)

#### Mode A: Color-Based Analysis (Always Available)
- Extracts dominant colors from images
- Analyzes brightness levels
- Generates simple descriptions like "A dark black item" or "A bright blue item"
- **Works offline, no API needed**

#### Mode B: Hugging Face API (Optional)
- Uses BLIP model via Hugging Face Inference API
- Provides detailed AI-generated captions
- Requires HF_API_TOKEN environment variable
- Falls back to Mode A if token not set or API fails

### 3. Semantic Search
- TF-IDF based similarity scoring
- Cosine similarity matching
- Generates embeddings on-the-fly if missing
- Same API interface as before

## Setup

### Install Dependencies

```bash
cd ml-service
pip install -r requirements.txt
```

All packages are Python 3.13 compatible.

### Environment Variables (Optional)

```bash
# Optional: For better image captioning via Hugging Face API
export HF_API_TOKEN="your_huggingface_token_here"
```

Get a free token at: https://huggingface.co/settings/tokens

### Start the Service

```bash
python main.py
```

Service runs on http://localhost:8000

## API Endpoints

All endpoints remain the same as before:

### POST /caption
Generate image description

**Request:** `multipart/form-data` with `file` field

**Response:**
```json
{
  "success": true,
  "caption": "A bright blue item.",
  "original_caption": "A bright blue item",
  "features": {
    "dominant_color": "blue",
    "brightness": 180.5,
    "size": [1024, 768]
  }
}
```

### POST /embedding
Generate text embedding (384 dimensions)

**Request:**
```json
{
  "text": "black backpack with laptop"
}
```

**Response:**
```json
{
  "success": true,
  "embedding": [0.123, 0.456, ...],
  "dimension": 384
}
```

### POST /embeddings/batch
Generate multiple embeddings

**Request:**
```json
{
  "texts": ["lost phone", "found wallet"]
}
```

### POST /search
Semantic search

**Request:**
```json
{
  "query": "blue notebook",
  "item_descriptions": [...]
}
```

### GET /health
Health check

**Response:**
```json
{
  "status": "healthy",
  "python_version": "3.13.5",
  "vectorizer_loaded": true,
  "hf_api_available": false
}
```

## Testing

### Test Health
```bash
curl http://localhost:8000/health
```

### Test Embedding
```bash
curl -X POST http://localhost:8000/embedding \
  -H "Content-Type: application/json" \
  -d '{"text": "black backpack with laptop"}'
```

### Test Image Caption
```bash
curl -X POST http://localhost:8000/caption \
  -F "file=@test-image.jpg"
```

## Advantages Over PyTorch Version

1. **Python 3.13 Compatible** - Works with latest Python
2. **Lightweight** - No heavy ML frameworks
3. **Fast Startup** - No model loading time
4. **Low Memory** - TF-IDF is extremely memory efficient
5. **No GPU Required** - Runs on any machine
6. **Offline Capable** - Works without internet (basic features)
7. **Simple Dependencies** - Easy to install and deploy

## Performance Notes

### Text Embeddings
- TF-IDF is very fast (microseconds per query)
- Works well for keyword-based matching
- Good for lost & found domain with specific terms

### Image Captioning
- Color-based: Instant, works offline
- HF API: 1-3 seconds, requires internet
- Automatically falls back if API unavailable

### Semantic Search
- Comparable to sentence-transformers for domain-specific queries
- Faster than neural models
- Pre-trained on lost & found vocabulary

## Migration Notes

The backend API expects the same response format, so **no backend changes needed**. The service maintains backward compatibility:

- Same endpoint paths
- Same request/response formats
- Same 384-dimensional embeddings
- Graceful degradation if features unavailable

## Docker Support

```bash
docker build -t lost-found-ml-py313 .
docker run -p 8000:8000 -e HF_API_TOKEN=your_token lost-found-ml-py313
```

## Troubleshooting

### Import Errors
Make sure you're using Python 3.13.5:
```bash
python --version  # Should show 3.13.5
```

### Low-Quality Captions
Set HF_API_TOKEN for better AI captions:
```bash
export HF_API_TOKEN="hf_..."
```

### Slow Search
If search is slow, ensure embeddings are pre-generated and stored in database (done automatically by backend).

## Future Enhancements

- Add more sophisticated color detection
- Support multiple Hugging Face models
- Cache API responses
- Add image similarity using color histograms
- Support OpenAI Vision API as alternative

## License

MIT
