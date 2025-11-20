from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from transformers import BlipProcessor, BlipForConditionalGeneration, AutoTokenizer, AutoModel
from sentence_transformers import SentenceTransformer
from PIL import Image
import torch
import io
import numpy as np
from pydantic import BaseModel
from typing import List
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Lost & Found ML Service")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global model variables
blip_processor = None
blip_model = None
sentence_model = None

@app.on_event("startup")
async def load_models():
    global blip_processor, blip_model, sentence_model

    try:
        logger.info("Loading BLIP model for image captioning...")
        blip_processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
        blip_model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base")

        device = "cuda" if torch.cuda.is_available() else "cpu"
        blip_model.to(device)
        logger.info(f"BLIP model loaded on {device}")

        logger.info("Loading sentence transformer for embeddings...")
        sentence_model = SentenceTransformer('all-MiniLM-L6-v2')
        logger.info("Sentence transformer loaded")

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

@app.get("/")
async def root():
    return {
        "message": "Lost & Found ML Service",
        "endpoints": {
            "image_caption": "/caption",
            "text_embedding": "/embedding",
            "semantic_search": "/search"
        }
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "blip_loaded": blip_model is not None,
        "sentence_model_loaded": sentence_model is not None
    }

@app.post("/caption")
async def generate_caption(file: UploadFile = File(...)):
    """Generate detailed description from uploaded image"""

    if blip_model is None or blip_processor is None:
        raise HTTPException(status_code=503, detail="BLIP model not loaded")

    try:
        contents = await file.read()
        image = Image.open(io.BytesIO(contents)).convert('RGB')

        device = "cuda" if torch.cuda.is_available() else "cpu"

        # Generate caption
        inputs = blip_processor(image, return_tensors="pt").to(device)

        # Generate with more tokens for detailed description
        out = blip_model.generate(**inputs, max_length=100, num_beams=5)
        caption = blip_processor.decode(out[0], skip_special_tokens=True)

        # Generate conditional caption with prompt for more details
        prompt = "A detailed description of the item:"
        conditional_inputs = blip_processor(image, text=prompt, return_tensors="pt").to(device)
        conditional_out = blip_model.generate(**conditional_inputs, max_length=100, num_beams=5)
        detailed_caption = blip_processor.decode(conditional_out[0], skip_special_tokens=True)

        # Combine captions for richer description
        if len(detailed_caption) > len(caption):
            final_caption = detailed_caption
        else:
            final_caption = caption

        # Enhance caption with context
        enhanced_caption = enhance_caption(final_caption)

        return {
            "success": True,
            "caption": enhanced_caption,
            "original_caption": caption
        }

    except Exception as e:
        logger.error(f"Error generating caption: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Caption generation failed: {str(e)}")

def enhance_caption(caption: str) -> str:
    """Enhance the caption with more structure"""
    # Capitalize first letter
    caption = caption.strip()
    if caption:
        caption = caption[0].upper() + caption[1:]

    # Add period if missing
    if caption and caption[-1] not in ['.', '!', '?']:
        caption += '.'

    return caption

@app.post("/embedding")
async def generate_embedding(request: TextRequest):
    """Generate embedding vector for text"""

    if sentence_model is None:
        raise HTTPException(status_code=503, detail="Sentence model not loaded")

    try:
        embedding = sentence_model.encode(request.text, convert_to_numpy=True)

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

    if sentence_model is None:
        raise HTTPException(status_code=503, detail="Sentence model not loaded")

    try:
        embeddings = sentence_model.encode(request.texts, convert_to_numpy=True)

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
    """Perform semantic search on item descriptions"""

    if sentence_model is None:
        raise HTTPException(status_code=503, detail="Sentence model not loaded")

    try:
        # Generate query embedding
        query_embedding = sentence_model.encode(request.query, convert_to_numpy=True)

        results = []

        for item in request.item_descriptions:
            # Check if item has embedding
            if 'embedding' not in item or not item['embedding']:
                # Generate embedding on the fly if missing
                description = f"{item.get('title', '')} {item.get('description', '')} {item.get('category', '')} {item.get('location', '')}"
                item_embedding = sentence_model.encode(description, convert_to_numpy=True)
            else:
                item_embedding = np.array(item['embedding'])

            # Calculate cosine similarity
            similarity = np.dot(query_embedding, item_embedding) / (
                np.linalg.norm(query_embedding) * np.linalg.norm(item_embedding)
            )

            results.append({
                "item_id": item.get('id', item.get('_id')),
                "similarity": float(similarity),
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
