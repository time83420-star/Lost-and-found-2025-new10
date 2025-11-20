# AI-Powered Similar Items Recommendation System

Complete implementation of Amazon-style "Similar Products" recommendation engine for the Lost & Found platform.

## Overview

The recommendation system uses **AI-powered semantic similarity** to suggest relevant items below each item details page. It leverages the existing ML service with Google Gemini embeddings (768-dimensional vectors) to compute similarity scores between items.

## Architecture

### Backend Layer

**New Endpoint**: `GET /api/items/:id/similar?limit=6`

**Controller**: `backend/controllers/itemController.js`
- New function: `getSimilarItems()`
- Uses existing embeddings stored in MongoDB
- Calls ML service for semantic similarity computation
- Filters results by similarity threshold (>0.4)
- Fallback to category/location matching if ML unavailable

**Routes**: `backend/routes/itemRoutes.js`
- Added route: `router.get('/:id/similar', getSimilarItems)`
- Public endpoint (no authentication required)

### Frontend Layer

**New Component**: `src/components/Items/SimilarItems.tsx`
- Fetches similar items from backend
- Displays in grid layout (3 columns on desktop)
- Shows AI-powered badge when using semantic search
- Displays match percentage for high-similarity items (>70%)
- Graceful loading and empty states

**Updated Page**: `src/pages/ItemDetails.tsx`
- Imports and renders `<SimilarItems />` component
- Placed below main item details
- Passes current item ID and limit parameter

### ML Service Integration

**Existing ML Service**: `ml-service/main.py`
- Already supports semantic search via `/search` endpoint
- Uses Google Gemini text-embedding-004 (768-dim)
- Hybrid scoring: 70% vector similarity + 20% keyword + 10% category
- Returns ranked results with similarity scores

## Features

### 1. AI-Powered Similarity

**Embedding-Based Matching**:
- Uses pre-generated 768-dimensional embeddings
- Computes cosine similarity between current item and all active items
- Filters by similarity threshold (0.4 minimum)
- Returns top 6 most similar items by default

**Hybrid Scoring Algorithm**:
```
final_score = 0.7 * vector_similarity + 0.2 * keyword_match + 0.1 * category_boost
```

### 2. Visual Indicators

**AI Badge**: Shows "AI-Powered Recommendations" when using semantic search

**Match Percentage**: Displays similarity score for high-confidence matches (>70%)
- Green badge with percentage
- Example: "85% Match"

**Loading State**: Animated spinner while fetching recommendations

### 3. Graceful Fallbacks

**ML Service Unavailable**:
- Falls back to category + location matching
- Returns items from same category or location
- No error shown to user

**No Embeddings**:
- If current item has no embedding, returns empty results
- Silently handles missing data

**No Similar Items**:
- Component renders nothing (null)
- Clean UX without empty state clutter

## API Documentation

### Get Similar Items

**Endpoint**: `GET /api/items/:id/similar`

**Parameters**:
- `id` (path): Item ID to find similar items for
- `limit` (query, optional): Max results to return (default: 6)

**Response**:
```json
{
  "items": [
    {
      "id": "64a1b2c3d4e5f6",
      "title": "Blue Backpack",
      "description": "Found near library",
      "category": "accessories",
      "location": "library",
      "type": "found",
      "imageUrl": "https://...",
      "similarity": 0.87,
      "confidence": "high",
      "user": {
        "id": "64a1...",
        "name": "John Doe",
        "email": "john@nitkkr.ac.in"
      },
      "createdAt": "2025-01-15T10:30:00Z"
    }
  ],
  "semantic": true,
  "count": 6
}
```

**Status Codes**:
- `200 OK`: Success
- `404 Not Found`: Item ID doesn't exist
- `500 Internal Server Error`: Server error

## Implementation Details

### Backend Logic Flow

```
1. Receive GET /api/items/:id/similar
2. Fetch current item from MongoDB
3. Check if item has embeddings
4. If no embeddings → return empty array
5. Fetch all active items (excluding current)
6. If no other items → return empty array
7. Try ML service semantic search:
   a. Build query text from title + description + category
   b. Call performSemanticSearch()
   c. Filter results by similarity > 0.4
   d. Limit to top N results
   e. Return with semantic: true
8. If ML fails → fallback:
   a. Filter by matching category OR location
   b. Limit to top N results
   c. Return with semantic: false
```

### Frontend Component Flow

```
1. Component mounts with currentItemId prop
2. useEffect triggers fetchSimilarItems()
3. Show loading spinner
4. Make GET request to /api/items/:id/similar
5. Parse response:
   - items array
   - semantic boolean
   - count number
6. Update state with results
7. Render:
   - If loading → spinner
   - If no items → null (hide component)
   - If items → grid of ItemCard components
8. Display AI badge if semantic: true
9. Show match percentage for items with similarity > 0.7
```

## Usage Examples

### Basic Usage

The component is automatically included on all item detail pages:

```tsx
// In ItemDetails.tsx
<SimilarItems currentItemId={item.id} limit={6} />
```

### Custom Limit

```tsx
<SimilarItems currentItemId={item.id} limit={10} />
```

### Testing Similarity

1. Create items with similar descriptions:
   - "Black laptop bag with charger"
   - "Dark computer backpack"
   - "Black bag for electronics"

2. Open any of these items

3. Similar items section shows related items with match scores

## Performance Considerations

### Caching

**ML Service LRU Cache**:
- 1000 embeddings cached
- 1 hour TTL
- ~80% hit rate for repeated queries

**Database Indexing**:
- Items indexed by status for fast active item queries
- User reference populated efficiently

### Optimization

**Query Efficiency**:
- Excludes current item from results (MongoDB filter)
- Only fetches active items (status: 'active')
- Uses lean() for faster MongoDB queries
- Limits result count to prevent large payloads

**Frontend Performance**:
- Component only renders if items exist
- Reuses existing ItemCard component
- Lazy loading via useEffect
- No unnecessary re-renders

## Testing Guide

### Manual Testing

**Test Semantic Similarity**:
```bash
# 1. Start ML service
cd ml-service
python main.py

# 2. Start backend
cd backend
npm run dev

# 3. Start frontend
npm run dev

# 4. Create test items via UI:
- Item 1: "Lost black backpack near library"
- Item 2: "Found dark bag in reading room"
- Item 3: "Blue notebook missing"

# 5. Open Item 1 details page
# 6. Scroll down to see "AI-Suggested Similar Items"
# 7. Item 2 should appear with high similarity (>70%)
```

**Test Fallback Mode**:
```bash
# 1. Stop ML service
# 2. Open any item details page
# 3. Similar items still appear (category/location based)
# 4. No "AI-Powered" badge shown
```

### API Testing

```bash
# Get similar items
curl http://localhost:5000/api/items/64a1b2c3d4e5f6/similar?limit=6

# Expected response
{
  "items": [...],
  "semantic": true,
  "count": 6
}
```

## Troubleshooting

### No Similar Items Showing

**Check**:
1. Current item has embeddings in database
2. Other active items exist with embeddings
3. ML service is running on port 8000
4. Backend can connect to ML service

**Debug**:
```bash
# Check item embeddings
mongosh
use nitkkr-lost-found
db.items.find({ embeddingGenerated: true }).count()

# Check ML service health
curl http://localhost:8000/health
```

### Low Similarity Scores

**Cause**: Items are semantically different

**Solution**:
- Lower threshold in backend (currently 0.4)
- Check if embeddings are properly generated
- Verify ML service is using Gemini API (better quality)

### ML Service Errors

**Check Logs**:
```bash
# Backend logs
cd backend
npm run dev
# Look for "ML similarity search failed" messages

# ML service logs
cd ml-service
python main.py
# Check for API errors
```

## Future Enhancements

### Potential Improvements

1. **Personalization**:
   - Track user browsing history
   - Weight recommendations by user interests
   - Boost items from same location as user

2. **Advanced Filtering**:
   - Filter by item type (lost/found)
   - Filter by date range (recent items)
   - Exclude already contacted items

3. **Performance**:
   - Pre-compute similarities offline
   - Store similarity matrix in Redis
   - Use vector database (Pinecone, Weaviate)

4. **UI Enhancements**:
   - Carousel/slider for many items
   - Hover to see full details
   - "Why recommended?" explanation tooltip

5. **Analytics**:
   - Track recommendation clicks
   - Measure conversion rate
   - A/B test different algorithms

## Integration Checklist

- [x] Backend controller function added
- [x] Backend route registered
- [x] Frontend component created
- [x] Frontend page updated
- [x] ML service integration tested
- [x] Build verification passed
- [x] Documentation complete

## Dependencies

**Backend**:
- Existing ML service (`backend/services/mlService.js`)
- MongoDB with embedding support
- Express.js routes

**Frontend**:
- React hooks (useState, useEffect)
- Existing ItemCard component
- Lucide React icons (Sparkles)
- Tailwind CSS for styling

**ML Service**:
- Google Gemini API (text-embedding-004)
- HuggingFace API (BLIP-2 for images)
- Python 3.13 compatible

## Summary

The AI-Powered Similar Items Recommendation System provides intelligent, context-aware item suggestions using state-of-the-art embedding technology. It enhances user experience by helping users discover relevant items they might have missed, increasing the chance of successful reunification of lost items with their owners.

**Key Benefits**:
- Increases user engagement
- Improves item discovery
- Leverages existing AI infrastructure
- Graceful degradation
- Production-ready code
- Zero configuration required

The system is now **fully operational** and ready for production use.
