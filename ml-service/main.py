# ml_service_hf_gemini_optionA.py
# Replace your existing ML service file with this.
# Uses HuggingFace Inference API (Salesforce/blip-image-captioning-base) for image captioning
# and Google Gemini embeddings (models/text-embedding-004) for semantic search.
#
# Requirements (Python 3.13 compatible):
#   fastapi, uvicorn, pillow, httpx, numpy, google-generativeai, python-multipart, pydantic
#
# Environment variables:
#   HF_API_TOKEN   -> (optional) HuggingFace token for better captions
#   HF_MODEL       -> (optional) default "Salesforce/blip-image-captioning-base"
#   GEMINI_API_KEY -> (required) Google Gemini API key for embeddings/search
#   PORT           -> (optional) port to run on (default 8000)
#
# NOTE: For quick local testing you can reference the uploaded file path below:
# TEST_FILE_PATH = "/mnt/data/report final.pdf"
# The runtime/tooling that serves files will convert this local path into a URL when needed.

import os
import io
import logging
import asyncio
from typing import List, Optional, Dict, Any

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from PIL import Image
import numpy as np
import httpx

import google.generativeai as genai

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ml_service_hf_gemini_optionA")

# ----------------- Configuration -----------------
HF_API_TOKEN = os.getenv("HF_API_TOKEN", "").strip()
HF_MODEL = os.getenv("HF_MODEL", "Salesforce/blip-image-captioning-base").strip()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
HF_API_URL = f"https://api-inference.huggingface.co/models/{HF_MODEL}"
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

# Example uploaded file path (tool will turn local path into URL for frontend testing)
# (Kept here per user's uploaded file usage; not required to run the service)
TEST_FILE_PATH = "/mnt/data/report final.pdf"

app = FastAPI(title="Lost & Found ML Service — HF (BLIP base) + Gemini (embeddings)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ----------------- Pydantic models -----------------
class TextRequest(BaseModel):
    text: str


class TextListRequest(BaseModel):
    texts: List[str]


class SearchRequest(BaseModel):
    query: str
    item_descriptions: List[dict]  # each dict: title, description, category, location, optional embedding, id/_id


# ----------------- Utilities -----------------
def _normalize_vector(vec: List[float]) -> List[float]:
    arr = np.array(vec, dtype=float)
    norm = np.linalg.norm(arr)
    if norm > 0:
        arr = arr / norm
    return [float(x) for x in arr.tolist()]


def _cosine_similarity(a: List[float], b: List[float]) -> float:
    a_np = np.array(a, dtype=float)
    b_np = np.array(b, dtype=float)
    if a_np.size == 0 or b_np.size == 0:
        return 0.0
    na = np.linalg.norm(a_np)
    nb = np.linalg.norm(b_np)
    if na == 0 or nb == 0:
        return 0.0
    return float(np.dot(a_np, b_np) / (na * nb))


def _enhance_caption(text: Optional[str]) -> str:
    if not text:
        return ""
    s = text.strip()
    if not s:
        return ""
    s = s[0].upper() + s[1:]
    if s[-1] not in ".!?":
        s += "."
    return s


# ----------------- HuggingFace (image captioning) -----------------
async def hf_caption_image(image_bytes: bytes, timeout: float = 30.0) -> Optional[str]:
    """
    Call HuggingFace Inference API for captioning (BLIP base).
    Returns caption string or None on failure.
    """
    if not HF_API_TOKEN:
        logger.debug("HF_API_TOKEN not configured; skipping HF caption.")
        return None

    headers = {"Authorization": f"Bearer {HF_API_TOKEN}"}
    # HF often expects bytes as content; using application/octet-stream
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.post(HF_API_URL, headers=headers, content=image_bytes)
            if resp.status_code == 200:
                data = resp.json()
                # common output shapes: list/dict/strings
                if isinstance(data, list) and len(data) > 0:
                    first = data[0]
                    if isinstance(first, dict):
                        # typical HF generated_text key
                        return first.get("generated_text") or first.get("caption") or None
                    if isinstance(first, str):
                        return first
                if isinstance(data, dict):
                    return data.get("generated_text") or data.get("caption") or data.get("text") or None
                # fallback to raw text
                if isinstance(data, str):
                    return data
            else:
                logger.warning(f"HuggingFace API error {resp.status_code}: {resp.text}")
    except Exception as e:
        logger.exception("Exception calling HuggingFace API for captioning: %s", e)
    return None


# ----------------- Gemini embeddings -----------------
async def _gemini_embed_text(text: str) -> List[float]:
    """
    Generate an embedding using Google Gemini (models/text-embedding-004).
    Uses asyncio.to_thread to avoid blocking the event loop.
    Returns a plain Python list of floats (normalized).
    """
    if not GEMINI_API_KEY:
        raise HTTPException(status_code=503, detail="GEMINI_API_KEY not configured")

    def embed_sync(t: str):
        # genai.embed_content returns a structure; adapt to common formats.
        res = genai.embed_content(model="models/text-embedding-004", content=t)
        # Attempt to extract embedding
        if isinstance(res, dict) and "embedding" in res:
            return res["embedding"]
        if isinstance(res, dict) and "data" in res:
            data = res["data"]
            if isinstance(data, list) and len(data) > 0 and "embedding" in data[0]:
                return data[0]["embedding"]
        if isinstance(res, list):
            return res
        raise RuntimeError("Unexpected Gemini embedding response format")

    emb = await asyncio.to_thread(embed_sync, text)
    return _normalize_vector(list(map(float, emb)))


# ----------------- Simple image feature fallback -----------------
def _extract_simple_image_features(image: Image.Image) -> dict:
    img = image.resize((100, 100))
    arr = np.array(img)
    avg_color = arr.mean(axis=(0, 1))
    r, g, b = avg_color
    if r > 150 and g < 100 and b < 100:
        color = "red"
    elif r < 100 and g > 150 and b < 100:
        color = "green"
    elif r < 100 and g < 100 and b > 150:
        color = "blue"
    elif r > 150 and g > 150 and b < 100:
        color = "yellow"
    elif r > 150 and g < 150 and b > 150:
        color = "purple"
    elif r < 100 and g > 150 and b > 150:
        color = "cyan"
    elif r > 200 and g > 200 and b > 200:
        color = "white"
    elif r < 100 and g < 100 and b < 100:
        color = "black"
    else:
        color = "multicolored"
    brightness = float(avg_color.mean())
    return {"dominant_color": color, "brightness": brightness, "size": image.size}


# ----------------- API Endpoints -----------------
@app.get("/")
async def root():
    return {
        "message": "Lost & Found ML Service (HuggingFace BLIP base + Gemini embeddings)",
        "endpoints": {
            "caption": "/caption",
            "embedding": "/embedding",
            "embeddings_batch": "/embeddings/batch",
            "search": "/search",
            "health": "/health",
        },
        "notes": "Set HF_API_TOKEN for improved captions; GEMINI_API_KEY is required for embeddings."
    }


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "hf_configured": bool(HF_API_TOKEN),
        "hf_model": HF_MODEL,
        "gemini_configured": bool(GEMINI_API_KEY),
    }


@app.post("/caption")
async def caption_endpoint(file: UploadFile = File(...)):
    """
    Accepts image file upload -> returns caption (HF if available) + fallback features.
    """
    try:
        contents = await file.read()
        image = Image.open(io.BytesIO(contents)).convert("RGB")
    except Exception as e:
        logger.exception("Invalid image upload")
        raise HTTPException(status_code=400, detail="Invalid image file")

    # Fallback simple features
    features = _extract_simple_image_features(image)
    brightness_label = "bright" if features["brightness"] > 150 else "dark"
    basic_caption = f"A {brightness_label} {features['dominant_color']} item"

    # Try HF caption
    hf_caption = await hf_caption_image(contents)
    if hf_caption:
        final_caption = _enhance_caption(hf_caption)
        original_caption = basic_caption
    else:
        final_caption = _enhance_caption(basic_caption)
        original_caption = basic_caption

    return {
        "success": True,
        "caption": final_caption,
        "original_caption": original_caption,
        "features": features
    }


@app.post("/embedding")
async def embedding_endpoint(request: TextRequest):
    """
    Generate Gemini embedding for a single text and return normalized vector.
    """
    text = request.text or ""
    if not text:
        raise HTTPException(status_code=400, detail="text is required")

    try:
        emb = await _gemini_embed_text(text)
        return {"success": True, "embedding": emb, "dimension": len(emb)}
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Embedding generation failed")
        raise HTTPException(status_code=500, detail=f"Embedding generation failed: {e}")


@app.post("/embeddings/batch")
async def embeddings_batch_endpoint(request: TextListRequest):
    """
    Batch embeddings for multiple texts in parallel (bounded concurrency).
    """
    texts = request.texts or []
    if not texts:
        raise HTTPException(status_code=400, detail="texts list is required")

    sem = asyncio.Semaphore(8)  # limit concurrency to avoid API throttling
    async def worker(t):
        async with sem:
            try:
                return await _gemini_embed_text(t)
            except Exception:
                logger.exception("Failed embedding for one text")
                return [0.0]  # fallback

    tasks = [worker(t) for t in texts]
    results = await asyncio.gather(*tasks)
    return {"success": True, "embeddings": results, "count": len(results)}


@app.post("/search")
async def search_endpoint(request: SearchRequest):
    """
    Semantic search:
    - get Gemini embedding for query
    - ensure each item has embedding (compute if not provided)
    - compute cosine similarity and return sorted results
    Expected items: list of dicts with optional 'embedding' (list of floats) and fields like title, description, category, location, id/_id
    """
    query = (request.query or "").strip()
    items = request.item_descriptions or []

    if not query:
        raise HTTPException(status_code=400, detail="query is required")

    try:
        # Query embedding
        q_emb = await _gemini_embed_text(query)
        q_arr = np.array(q_emb, dtype=float)

        # Prepare tasks for items that need embeddings
        embed_tasks = []
        for idx, item in enumerate(items):
            if item.get("embedding"):
                continue
            # build description text
            desc = " ".join([
                str(item.get("title", "")),
                str(item.get("description", "")),
                str(item.get("category", "")),
                str(item.get("location", ""))
            ]).strip()
            if not desc:
                desc = "item"
            embed_tasks.append((idx, desc))

        # compute missing embeddings concurrently with bounded concurrency
        results_map = {}
        if embed_tasks:
            sem = asyncio.Semaphore(6)
            async def embed_item(idx, text):
                async with sem:
                    try:
                        emb = await _gemini_embed_text(text)
                        results_map[idx] = emb
                    except Exception:
                        results_map[idx] = [0.0] * len(q_emb)

            await asyncio.gather(*[embed_item(i, d) for i, d in embed_tasks])

        # compute similarity
        results = []
        for idx, item in enumerate(items):
            if item.get("embedding"):
                try:
                    emb = np.array(item["embedding"], dtype=float)
                    # normalize
                    if emb.size != q_arr.size:
                        # if shape mismatch, try to fallback to computing embedding from text fields
                        emb = np.array(results_map.get(idx, [0.0]*len(q_emb)), dtype=float)
                    else:
                        nrm = np.linalg.norm(emb)
                        if nrm > 0:
                            emb = emb / nrm
                except Exception:
                    emb = np.array(results_map.get(idx, [0.0]*len(q_emb)), dtype=float)
            else:
                emb = np.array(results_map.get(idx, [0.0]*len(q_emb)), dtype=float)

            # ensure shapes match
            if emb.size != q_arr.size:
                sim = 0.0
            else:
                sim = float(np.dot(q_arr, emb))
            results.append({
                "item_id": item.get("id", item.get("_id")),
                "similarity": sim,
                "title": item.get("title", ""),
                "description": item.get("description", ""),
                "category": item.get("category", ""),
                "location": item.get("location", ""),
                "type": item.get("type", ""),
                "imageUrl": item.get("imageUrl", ""),
                "createdAt": item.get("createdAt", ""),
                "user": item.get("user", {})
            })

        # sort results by similarity desc
        results.sort(key=lambda x: x["similarity"], reverse=True)
        return {"success": True, "results": results, "count": len(results)}
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Semantic search failed")
        raise HTTPException(status_code=500, detail=f"Semantic search failed: {e}")


# ----------------- Run server (when executed directly) -----------------
if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("ml_service_hf_gemini_optionA:app", host="0.0.0.0", port=port, reload=True)
