# Machine Learning Integration Guide

Complete ML features integrated into the Lost & Found system using BLIP and sentence-transformers.

## Architecture

### ML Service (Python FastAPI)
- **Location**: `ml-service/`
- **Port**: 8000
- **Models**:
  - BLIP (Salesforce/blip-image-captioning-base) for image captioning
  - all-MiniLM-L6-v2 for text embeddings

### Backend Integration (Node.js)
- **ML Service Client**: `backend/services/mlService.js`
- **Endpoints**: Upload, Item Creation, Search

### Frontend Integration (React)
- **Auto-caption on upload**: `src/pages/UploadItem.tsx`
- **Semantic search**: `src/pages/BrowseItems.tsx`

## Features

### 1. AI Image Captioning

**Flow**: Upload Image → ML Service → BLIP Model → Auto Description

**Backend**: `backend/controllers/uploadController.js`
- Sends image buffer to ML service
- Returns both Cloudinary URL and AI caption
- Graceful fallback if ML service unavailable

**Frontend**: `src/pages/UploadItem.tsx`
- Shows loading spinner during caption generation
- Auto-fills description field
- User can edit generated caption
- Stored as `aiGeneratedDescription` in database

### 2. Text Embeddings

**Flow**: Create Item → Generate Embedding → Store in MongoDB

**Backend**: `backend/controllers/itemController.js`
- Combines title, description, category, location
- Generates 384-dimensional vector
- Stores in `embedding` array field
- Sets `embeddingGenerated` flag

**Database**: `backend/models/Item.js`
```javascript
embedding: [Number],        // 384-dim vector
embeddingGenerated: Boolean,
aiGeneratedDescription: String
```

### 3. Semantic Search

**Flow**: Search Query → Generate Query Embedding → Cosine Similarity → Ranked Results

**Backend**: `backend/controllers/itemController.js`
- Accepts `useSemanticSearch` parameter
- Calls ML service with query and all items
- Filters results by similarity threshold (>0.3)
- Falls back to regex search if ML fails

**Frontend**: `src/pages/BrowseItems.tsx`
- Checkbox to enable/disable semantic search
- Shows "Semantic Results" badge
- Success toast when using AI search

## Setup Instructions

### 1. Install ML Service Dependencies

```bash
cd ml-service
pip install -r requirements.txt
```

### 2. Start ML Service

```bash
cd ml-service
python main.py
```

Service runs on http://localhost:8000

### 3. Update Backend Environment

```bash
# backend/.env or project root
ML_SERVICE_URL=http://localhost:8000
```

### 4. Install Backend Dependencies

```bash
cd backend
npm install form-data
```

### 5. Start Backend

```bash
cd backend
npm run dev
```

### 6. Start Frontend

```bash
npm run dev
```

## API Endpoints

### ML Service

**POST /caption**
- Body: multipart/form-data with `file`
- Response: `{ success: true, caption: string, original_caption: string }`

**POST /embedding**
- Body: `{ text: string }`
- Response: `{ success: true, embedding: number[], dimension: 384 }`

**POST /embeddings/batch**
- Body: `{ texts: string[] }`
- Response: `{ success: true, embeddings: number[][], count: number }`

**POST /search**
- Body: `{ query: string, item_descriptions: object[] }`
- Response: `{ success: true, results: object[], count: number }`

**GET /health**
- Response: `{ status: string, blip_loaded: boolean, sentence_model_loaded: boolean }`

### Backend

**POST /api/upload**
- Returns: `{ url: string, aiCaption?: string }`

**POST /api/items**
- Accepts: `aiGeneratedDescription` field
- Automatically generates embeddings

**POST /api/items/search**
- Accepts: `{ query: string, useSemanticSearch: boolean }`
- Returns: `{ items: object[], semantic: boolean, count?: number }`

## Features Breakdown

### Image Caption Generation
1. User uploads image
2. Backend uploads to Cloudinary
3. Backend sends image buffer to ML service
4. BLIP generates detailed caption
5. Frontend auto-fills description
6. User can edit before saving

### Embedding Generation
1. User creates item
2. Backend combines text fields
3. ML service generates 384-dim vector
4. Vector stored in MongoDB
5. Flag `embeddingGenerated: true`

### Semantic Search
1. User enters search query
2. ML service generates query embedding
3. Compute cosine similarity with all items
4. Return ranked results (similarity > 0.3)
5. Show "Semantic Results" indicator

## Performance Optimizations

### Non-blocking Fallbacks
- If ML service fails, continue without AI features
- Caption generation: Continue with empty caption
- Embedding generation: Save item without embedding
- Semantic search: Fall back to regex search

### Caching
- ML models loaded once on startup
- Embeddings stored in database
- No re-computation needed

### Timeouts
- ML service calls: 30 second timeout
- Batch operations: 60 second timeout
- Health checks: 5 second timeout

## Error Handling

### ML Service Down
- Upload: Returns URL without caption
- Item creation: Saves without embedding
- Search: Falls back to regex

### Invalid Input
- Empty query: 400 error
- No file: 400 error
- Invalid image: ML service error

### Network Issues
- Timeout after 30 seconds
- Graceful degradation
- User-friendly error messages

## Model Details

### BLIP (Image Captioning)
- Model: Salesforce/blip-image-captioning-base
- Input: RGB image (any size)
- Output: Natural language description
- Max length: 100 tokens
- Beam search: 5 beams

### Sentence Transformer (Embeddings)
- Model: all-MiniLM-L6-v2
- Input: Text string
- Output: 384-dimensional vector
- Normalized embeddings
- Cosine similarity for search

### Similarity Threshold
- Minimum similarity: 0.3
- Range: 0.0 (no match) to 1.0 (perfect match)
- Results sorted by similarity (descending)

## Testing

### Test Image Caption
```bash
curl -X POST http://localhost:8000/caption \
  -F "file=@test-image.jpg"
```

### Test Embedding
```bash
curl -X POST http://localhost:8000/embedding \
  -H "Content-Type: application/json" \
  -d '{"text": "black backpack with laptop"}'
```

### Test Search
```bash
curl -X POST http://localhost:8000/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "blue notebook",
    "item_descriptions": [
      {"id": "1", "title": "Blue Notebook", "description": "Found in library", "embedding": [...]}
    ]
  }'
```

## Production Deployment

### Docker
```bash
cd ml-service
docker build -t lost-found-ml .
docker run -p 8000:8000 lost-found-ml
```

### Environment Variables
```bash
# Backend
ML_SERVICE_URL=https://ml-service.example.com

# ML Service
ML_SERVICE_PORT=8000
ML_SERVICE_HOST=0.0.0.0
```

### Scaling
- Use GPU for faster inference
- Deploy ML service separately
- Use load balancer for multiple instances
- Cache embeddings in Redis

## Monitoring

### Health Check
```bash
curl http://localhost:8000/health
```

### Logs
- ML service: Python logging
- Backend: Console logs for ML calls
- Frontend: Toast notifications

## Limitations

### Current Limitations
- Single image per item
- English language only
- No image-to-image similarity
- No multi-modal search

### Future Enhancements
- Multi-image support
- Hindi language support
- Image similarity search
- Voice search integration
- Real-time embedding updates

## Troubleshooting

### ML Service Won't Start
- Check Python version (3.10+)
- Install all dependencies
- Verify CUDA for GPU support

### Caption Not Generated
- Check ML service health
- Verify image format (JPEG/PNG)
- Check network connectivity

### Semantic Search Not Working
- Verify `useSemanticSearch: true`
- Check embeddings in database
- Verify ML service running

### Slow Performance
- Use GPU for inference
- Cache embeddings
- Reduce similarity threshold
- Limit search results

## Files Modified/Created

### ML Service (New)
- `ml-service/main.py`
- `ml-service/requirements.txt`
- `ml-service/Dockerfile`
- `ml-service/README.md`

### Backend
- `backend/models/Item.js` (updated)
- `backend/services/mlService.js` (new)
- `backend/controllers/uploadController.js` (updated)
- `backend/controllers/itemController.js` (updated)
- `backend/package.json` (updated)

### Frontend
- `src/pages/UploadItem.tsx` (updated)
- `src/pages/BrowseItems.tsx` (updated)
- `src/utils/api.ts` (updated)

## Summary

Full ML integration with:
- BLIP-based image captioning
- Sentence transformer embeddings
- Semantic search with cosine similarity
- Graceful fallbacks
- User-friendly UI
- Production-ready architecture
