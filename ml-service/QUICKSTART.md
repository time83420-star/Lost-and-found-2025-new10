# Quick Start - ML Service Python 3.13

## Installation

```bash
cd ml-service

# Install dependencies
pip install -r requirements.txt

# Verify installation
python --version  # Should show 3.13.x
```

## Start Service

```bash
python main.py
```

Service will be available at: http://localhost:8000

## Test It

```bash
# Health check
curl http://localhost:8000/health

# Test embedding
curl -X POST http://localhost:8000/embedding \
  -H "Content-Type: application/json" \
  -d '{"text": "lost black backpack"}'
```

## What's Different?

This version uses:
- **scikit-learn** instead of PyTorch/sentence-transformers
- **TF-IDF** for text embeddings (384 dimensions)
- **Color analysis** for image captions (offline)
- **Optional HF API** for better captions (online)

All Python 3.13.5 compatible!

## Optional: Better Image Captions

```bash
export HF_API_TOKEN="your_token_here"
python main.py
```

Get token at: https://huggingface.co/settings/tokens
