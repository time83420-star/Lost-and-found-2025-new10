# Testing the Refactored ML Service

## Prerequisites

- Python 3.13.5 installed
- pip working

## Installation Test

```bash
cd ml-service
pip install -r requirements.txt
```

Expected output: All packages install successfully with no errors.

## Startup Test

```bash
python main.py
```

Expected output:
```
INFO:     Started server process [xxxxx]
INFO:     Waiting for application startup.
INFO:     Initializing TF-IDF vectorizer for text embeddings...
INFO:     TF-IDF vectorizer initialized successfully
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

## API Tests

### 1. Health Check
```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "python_version": "3.13.5",
  "vectorizer_loaded": true,
  "hf_api_available": false
}
```

### 2. Root Endpoint
```bash
curl http://localhost:8000/
```

Expected response:
```json
{
  "message": "Lost & Found ML Service - Python 3.13 Compatible",
  "python_version": "3.13.5",
  "endpoints": {
    "image_caption": "/caption",
    "text_embedding": "/embedding",
    "semantic_search": "/search"
  },
  "features": {
    "image_captioning": "Color-based + optional HF API",
    "text_embeddings": "TF-IDF (384 dimensions)",
    "semantic_search": "Cosine similarity"
  }
}
```

### 3. Text Embedding
```bash
curl -X POST http://localhost:8000/embedding \
  -H "Content-Type: application/json" \
  -d '{"text": "black backpack with laptop"}'
```

Expected response:
```json
{
  "success": true,
  "embedding": [0.123, 0.456, ...],  // 384 numbers
  "dimension": 384
}
```

### 4. Batch Embeddings
```bash
curl -X POST http://localhost:8000/embeddings/batch \
  -H "Content-Type: application/json" \
  -d '{"texts": ["lost phone", "found wallet", "blue notebook"]}'
```

Expected response:
```json
{
  "success": true,
  "embeddings": [[...], [...], [...]],  // 3 arrays of 384 numbers
  "count": 3
}
```

### 5. Image Caption (Create test image first)
```bash
# Create a simple test image
python3 << 'PYTHON'
from PIL import Image
import numpy as np

# Create a blue test image
img = Image.new('RGB', (200, 200), color='blue')
img.save('test-blue.jpg')
print("Created test-blue.jpg")
PYTHON

# Test caption endpoint
curl -X POST http://localhost:8000/caption \
  -F "file=@test-blue.jpg"
```

Expected response:
```json
{
  "success": true,
  "caption": "A bright blue item.",
  "original_caption": "A bright blue item",
  "features": {
    "dominant_color": "blue",
    "brightness": 127.5,
    "size": [200, 200]
  }
}
```

### 6. Semantic Search
```bash
curl -X POST http://localhost:8000/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "blue bag",
    "item_descriptions": [
      {
        "id": "1",
        "title": "Blue Backpack",
        "description": "Lost blue backpack in library",
        "category": "accessories",
        "location": "library",
        "type": "lost"
      },
      {
        "id": "2",
        "title": "Red Wallet",
        "description": "Found red wallet in canteen",
        "category": "accessories",
        "location": "canteen",
        "type": "found"
      }
    ]
  }'
```

Expected response:
```json
{
  "success": true,
  "results": [
    {
      "item_id": "1",
      "similarity": 0.85,
      "title": "Blue Backpack",
      "description": "Lost blue backpack in library",
      ...
    },
    {
      "item_id": "2",
      "similarity": 0.12,
      "title": "Red Wallet",
      ...
    }
  ],
  "count": 2
}
```

## Performance Benchmarks

Run these to verify speed:

```bash
# Embedding speed test
time for i in {1..100}; do
  curl -s -X POST http://localhost:8000/embedding \
    -H "Content-Type: application/json" \
    -d '{"text": "test item"}' > /dev/null
done
```

Expected: Should complete 100 requests in <5 seconds

## Integration with Backend

The backend Node.js service should work without changes. Test by:

1. Start ML service: `python main.py` (port 8000)
2. Start backend: `cd backend && npm run dev` (port 5000)
3. Upload an item with image via frontend
4. Check that:
   - Image caption is generated
   - Text embeddings are stored
   - Semantic search works

## Troubleshooting

### Import Error: No module named 'sklearn'
```bash
pip install scikit-learn
```

### Import Error: No module named 'PIL'
```bash
pip install pillow
```

### Port 8000 already in use
```bash
# Kill process on port 8000
lsof -ti:8000 | xargs kill -9

# Or change port
export ML_SERVICE_PORT=8001
python main.py
```

## Docker Test

```bash
cd ml-service
docker build -t ml-service-py313 .
docker run -p 8000:8000 ml-service-py313
```

Then test with curl commands above.

## Success Criteria

All tests should:
- Return 200 status codes
- Return expected JSON structure
- Complete in reasonable time (<1 second for embeddings, <5 seconds for images)
- Work without errors in logs
