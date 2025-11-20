from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image
import io
import numpy as np
from pydantic import BaseModel
from typing import List, Optional
import logging
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import base64
import httpx
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Lost & Found ML Service - Python 3.13 Compatible")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global vectorizer for text embeddings
vectorizer = None
corpus_texts = []

# Hugging Face API settings (optional - for image captioning)
HF_API_TOKEN = os.getenv("HF_API_TOKEN", "")
HF_API_URL = "https://api-inference.huggingface.co/models/Salesforce/blip-image-captioning-base"


@app.on_event("startup")
async def load_models():
    global vectorizer, corpus_texts

    try:
        logger.info("Initializing TF-IDF vectorizer for text embeddings...")
        vectorizer = TfidfVectorizer(
            max_features=384,  # Match the dimension from sentence-transformers
            ngram_range=(1, 2),
            stop_words='english',
            sublinear_tf=True
        )

        # Initialize with some common lost & found terms
        corpus_texts = [
            "lost phone mobile device electronics",
            "found wallet money cards accessories",
            "black backpack bag accessories",
            "blue notebook book library",
            "keys keychain metal accessories",
            "laptop computer electronics device",
            "water bottle drink container",
            "umbrella rain weather accessories",
            "glasses spectacles vision accessories",
            "watch clock time jewelry accessories",
            "headphones earphones audio electronics",
            "charger cable wire electronics",
            "id card identity document badge",
            "jacket coat clothing winter",
            "book textbook library academic"
        ]

        vectorizer.fit(corpus_texts)
        logger.info("TF-IDF vectorizer initialized successfully")

    except Exception as e:
        logger.error(f"Error loading models: {str(e)}")
        raise


class TextRequest(BaseModel):
    text: str


class TextListRequest(BaseModel):
    texts: List[str]


class SearchRequest(BaseModel):
    query: str
    item_descriptions: List[dict]


def extract_image_features(image: Image.Image) -> dict:
    """Extract basic features from image for description"""
    features = {}

    # Get dominant colors
    img_array = np.array(image.resize((100, 100)))

    # Calculate average color
    avg_color = img_array.mean(axis=(0, 1))

    # Determine dominant color name
    r, g, b = avg_color
    if r > 150 and g < 100 and b < 100:
        color_name = "red"
    elif r < 100 and g > 150 and b < 100:
        color_name = "green"
    elif r < 100 and g < 100 and b > 150:
        color_name = "blue"
    elif r > 150 and g > 150 and b < 100:
        color_name = "yellow"
    elif r > 150 and g < 150 and b > 150:
        color_name = "purple"
    elif r < 100 and g > 150 and b > 150:
        color_name = "cyan"
    elif r > 200 and g > 200 and b > 200:
        color_name = "white"
    elif r < 100 and g < 100 and b < 100:
        color_name = "black"
    else:
        color_name = "multicolored"

    features['dominant_color'] = color_name
    features['brightness'] = float(avg_color.mean())
    features['size'] = image.size

    return features


async def query_huggingface_api(image_bytes: bytes) -> Optional[str]:
    """Query Hugging Face Inference API for image captioning"""
    if not HF_API_TOKEN:
        logger.warning("HF_API_TOKEN not set, skipping API call")
        return None

    try:
        headers = {"Authorization": f"Bearer {HF_API_TOKEN}"}

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                HF_API_URL,
                headers=headers,
                data=image_bytes
            )

            if response.status_code == 200:
                result = response.json()
                if isinstance(result, list) and len(result) > 0:
                    return result[0].get('generated_text', '')
            else:
                logger.warning(f"HF API returned status {response.status_code}")

    except Exception as e:
        logger.error(f"Error querying Hugging Face API: {str(e)}")

    return None


@app.get("/")
async def root():
    return {
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


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "python_version": "3.13.5",
        "vectorizer_loaded": vectorizer is not None,
        "hf_api_available": bool(HF_API_TOKEN)
    }


@app.post("/caption")
async def generate_caption(file: UploadFile = File(...)):
    """Generate description from uploaded image using color analysis + optional HF API"""

    try:
        contents = await file.read()
        image = Image.open(io.BytesIO(contents)).convert('RGB')

        # Extract basic features
        features = extract_image_features(image)

        # Build basic description from features
        color = features['dominant_color']
        brightness = "bright" if features['brightness'] > 150 else "dark"

        basic_caption = f"A {brightness} {color} item"

        # Try to get better caption from HF API if available
        api_caption = await query_huggingface_api(contents)

        if api_caption:
            final_caption = enhance_caption(api_caption)
            original_caption = basic_caption
        else:
            final_caption = enhance_caption(basic_caption)
            original_caption = basic_caption

        return {
            "success": True,
            "caption": final_caption,
            "original_caption": original_caption,
            "features": features
        }

    except Exception as e:
        logger.error(f"Error generating caption: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Caption generation failed: {str(e)}")


def enhance_caption(caption: str) -> str:
    """Enhance the caption with proper formatting"""
    caption = caption.strip()
    if caption:
        caption = caption[0].upper() + caption[1:]

    if caption and caption[-1] not in ['.', '!', '?']:
        caption += '.'

    return caption


@app.post("/embedding")
async def generate_embedding(request: TextRequest):
    """Generate TF-IDF embedding vector for text"""

    if vectorizer is None:
        raise HTTPException(status_code=503, detail="Vectorizer not loaded")

    try:
        # Transform text to TF-IDF vector
        embedding = vectorizer.transform([request.text]).toarray()[0]

        # Normalize to unit vector (similar to sentence-transformers)
        norm = np.linalg.norm(embedding)
        if norm > 0:
            embedding = embedding / norm

        return {
            "success": True,
            "embedding": embedding.tolist(),
            "dimension": len(embedding)
        }

    except Exception as e:
        logger.error(f"Error generating embedding: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Embedding generation failed: {str(e)}")


@app.post("/embeddings/batch")
async def generate_embeddings_batch(request: TextListRequest):
    """Generate embeddings for multiple texts"""

    if vectorizer is None:
        raise HTTPException(status_code=503, detail="Vectorizer not loaded")

    try:
        # Transform texts to TF-IDF vectors
        embeddings = vectorizer.transform(request.texts).toarray()

        # Normalize each vector
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        norms[norms == 0] = 1  # Avoid division by zero
        embeddings = embeddings / norms

        return {
            "success": True,
            "embeddings": embeddings.tolist(),
            "count": len(embeddings)
        }

    except Exception as e:
        logger.error(f"Error generating batch embeddings: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Batch embedding generation failed: {str(e)}")


@app.post("/search")
async def semantic_search(request: SearchRequest):
    """Perform semantic search using TF-IDF and cosine similarity"""

    if vectorizer is None:
        raise HTTPException(status_code=503, detail="Vectorizer not loaded")

    try:
        # Generate query embedding
        query_embedding = vectorizer.transform([request.query]).toarray()[0]

        # Normalize query vector
        query_norm = np.linalg.norm(query_embedding)
        if query_norm > 0:
            query_embedding = query_embedding / query_norm

        results = []

        for item in request.item_descriptions:
            # Check if item has embedding
            if 'embedding' not in item or not item['embedding']:
                # Generate embedding on the fly
                description = f"{item.get('title', '')} {item.get('description', '')} {item.get('category', '')} {item.get('location', '')}"
                item_embedding = vectorizer.transform([description]).toarray()[0]

                # Normalize
                item_norm = np.linalg.norm(item_embedding)
                if item_norm > 0:
                    item_embedding = item_embedding / item_norm
            else:
                item_embedding = np.array(item['embedding'])

            # Calculate cosine similarity
            similarity = float(np.dot(query_embedding, item_embedding))

            results.append({
                "item_id": item.get('id', item.get('_id')),
                "similarity": similarity,
                "title": item.get('title', ''),
                "description": item.get('description', ''),
                "category": item.get('category', ''),
                "location": item.get('location', ''),
                "type": item.get('type', ''),
                "imageUrl": item.get('imageUrl', ''),
                "createdAt": item.get('createdAt', ''),
                "user": item.get('user', {})
            })

        # Sort by similarity (highest first)
        results.sort(key=lambda x: x['similarity'], reverse=True)

        return {
            "success": True,
            "results": results,
            "count": len(results)
        }

    except Exception as e:
        logger.error(f"Error performing semantic search: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Semantic search failed: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
