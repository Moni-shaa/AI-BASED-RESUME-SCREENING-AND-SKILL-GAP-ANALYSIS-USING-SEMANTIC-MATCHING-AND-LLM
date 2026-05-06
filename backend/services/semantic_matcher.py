from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

# Load lightweight model
model = SentenceTransformer("all-MiniLM-L6-v2")

def calculate_semantic_similarity(resume_text, jd_text):
    """
    Calculate semantic similarity between resume and job description
    using sentence embeddings.
    """
    resume_embedding = model.encode([resume_text])
    jd_embedding = model.encode([jd_text])

    similarity = cosine_similarity(resume_embedding, jd_embedding)[0][0]

    return round(float(similarity) * 100, 2)