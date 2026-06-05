from sentence_transformers import SentenceTransformer

model = SentenceTransformer('all-MiniLM-L6-v2')

def get_embeddings(texts):
    """Generate embeddings for a list of texts."""
    return model.encode(texts, convert_to_numpy=True)
