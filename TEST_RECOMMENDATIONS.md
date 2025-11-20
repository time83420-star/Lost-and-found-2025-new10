# Testing the AI Recommendation System

Quick guide to test the new "AI-Suggested Similar Items" feature.

## Prerequisites

Ensure all services are running:

```bash
# Terminal 1 - ML Service
cd ml-service
python main.py
# Should see: Uvicorn running on http://0.0.0.0:8000

# Terminal 2 - Backend
cd backend
npm run dev
# Should see: Server running on port 5000

# Terminal 3 - Frontend
npm run dev
# Should see: Local: http://localhost:5173
```

## Test Scenario 1: High Similarity Items

### Step 1: Create Similar Items

1. Login/Register at http://localhost:5173
2. Upload 3 items with similar descriptions:

**Item A**:
- Title: "Black Laptop Bag"
- Category: Accessories
- Location: Library
- Description: "Lost black laptop bag with charger and mouse inside. Has NIT logo on front."
- Upload any image

**Item B**:
- Title: "Dark Computer Backpack"
- Category: Accessories
- Location: Academic Block
- Description: "Found dark backpack containing laptop accessories and electronics."
- Upload any image

**Item C**:
- Title: "Blue Water Bottle"
- Category: Other
- Location: Canteen
- Description: "Found blue water bottle near cafeteria counter."
- Upload any image

### Step 2: View Recommendations

1. Navigate to Browse Items
2. Click on "Black Laptop Bag" (Item A)
3. Scroll down below the item details
4. You should see:
   - Section titled "AI-Suggested Similar Items"
   - "AI-Powered Recommendations" badge
   - Item B ("Dark Computer Backpack") with high similarity (70%+ match)
   - Item C should NOT appear (low similarity)

### Expected Results

**Item B Match Score**: 75-90% (high semantic similarity)
- Both mention laptop/computer
- Both mention backpack/bag
- Both mention accessories/electronics

**Visual Indicators**:
- Green badge showing "85% Match" (or similar)
- "AI-Powered Recommendations" badge in header
- Clean grid layout with 3 columns on desktop

## Test Scenario 2: Category-Based Fallback

### Step 1: Stop ML Service

```bash
# Stop the ML service in Terminal 1
Ctrl+C
```

### Step 2: Test Fallback

1. Refresh the item details page
2. Similar items still appear
3. NO "AI-Powered Recommendations" badge
4. Items filtered by category and location

### Expected Results

- System gracefully falls back to simple matching
- No errors shown to user
- Items from same category appear
- Slightly less relevant results

## Test Scenario 3: No Similar Items

### Setup

1. Create a unique item:
   - Title: "Purple Vintage Calculator"
   - Category: Other
   - Location: Sports Complex
   - Description: "Rare purple vintage calculator from 1980s"

2. Make sure no other items exist with similar attributes

### Expected Results

- No "Similar Items" section appears
- Page looks clean (not cluttered with empty section)
- No errors in console

## Test Scenario 4: Many Similar Items

### Setup

Create 10+ items all with similar descriptions:
- "Black backpack" variations
- All in "Accessories" category
- Various locations

### Expected Results

- Only top 6 similar items shown (default limit)
- Sorted by similarity score (highest first)
- Match percentages vary (60%-95%)

## API Testing

### Direct API Calls

```bash
# Get item ID from MongoDB or browser
ITEM_ID="64a1b2c3d4e5f6"

# Test similar items endpoint
curl http://localhost:5000/api/items/$ITEM_ID/similar?limit=6

# Expected response
{
  "items": [
    {
      "id": "...",
      "title": "...",
      "similarity": 0.87,
      "confidence": "high"
    }
  ],
  "semantic": true,
  "count": 6
}
```

### Test with Different Limits

```bash
# Get 3 similar items
curl http://localhost:5000/api/items/$ITEM_ID/similar?limit=3

# Get 10 similar items
curl http://localhost:5000/api/items/$ITEM_ID/similar?limit=10
```

## Verification Checklist

- [ ] Similar items section appears below item details
- [ ] AI badge shows when ML service is running
- [ ] Match percentages display for high-similarity items (>70%)
- [ ] Loading spinner shows while fetching
- [ ] Clicking similar item navigates to that item's details
- [ ] New similar items load when viewing different item
- [ ] Fallback works when ML service is down
- [ ] No errors in browser console
- [ ] No errors in backend logs
- [ ] Mobile responsive layout works

## Common Issues

### Issue: No similar items showing

**Check**:
```bash
# Verify embeddings exist
mongosh
use nitkkr-lost-found
db.items.find({ embeddingGenerated: true }).count()
# Should return count > 0

# Check ML service
curl http://localhost:8000/health
# Should return status: "healthy"
```

### Issue: Low similarity scores

**Cause**: Items are genuinely different

**Test**: Create items with nearly identical descriptions and verify high similarity

### Issue: "AI-Powered" badge not showing

**Check**:
- ML service running on port 8000
- Backend can reach ML service
- Items have embeddings in database
- Check backend logs for ML errors

## Performance Testing

### Load Test

```bash
# Create 100 items
# Open any item details page
# Measure load time for similar items section
# Should be < 2 seconds
```

### Cache Testing

```bash
# Open same item multiple times
# Second load should be faster (cached embeddings)
# Check ML service logs for cache hits
```

## Success Criteria

The recommendation system is working correctly if:

1. Similar items appear below each item details page
2. Similarity scores are logical (related items have high scores)
3. AI badge appears when using semantic search
4. System works without ML service (fallback)
5. No errors in console or logs
6. Build completes successfully
7. UI is responsive and professional

## Next Steps

After successful testing:

1. Deploy ML service to production
2. Deploy backend with new endpoint
3. Deploy frontend with new component
4. Monitor similarity quality in production
5. Gather user feedback
6. Iterate on similarity threshold if needed

## Debug Commands

```bash
# Check backend logs
cd backend
npm run dev | grep -i "similar"

# Check ML service logs
cd ml-service
python main.py | grep -i "search"

# Check MongoDB embeddings
mongosh
use nitkkr-lost-found
db.items.find({ embeddingGenerated: true }).limit(5).pretty()

# Test ML service directly
curl -X POST http://localhost:8000/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "black laptop bag",
    "item_descriptions": [],
    "threshold": 0.4,
    "use_hybrid": true
  }'
```

## Expected User Experience

**User Flow**:
1. User views lost item: "Black Backpack"
2. Scrolls down below description
3. Sees "AI-Suggested Similar Items" with sparkle icon
4. Notices "AI-Powered Recommendations" badge
5. Sees 3-6 similar items in grid
6. One item shows "87% Match" in green
7. Clicks on similar item
8. Views that item's details
9. New similar items load for this item

**Benefits**:
- Discovers items they might have missed
- Finds alternate matches if exact item not listed
- Increases engagement with platform
- Professional AI-powered experience

The recommendation system is now ready for production use!
