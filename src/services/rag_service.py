"""
NCERT RAG & Vector Retrieval Service
Integrates verified NCERT textbook chunks, NVIDIA Nemotron embeddings (2048-dim),
and Supabase pgvector cosine similarity search with local fallback.
"""

import os
import math
import requests
from typing import List, Dict, Any, Optional
try:
    import psycopg2
except ImportError:
    psycopg2 = None
from dotenv import load_dotenv

from src.storage.remediation_repository import RemediationRepository

load_dotenv()


class RAGService:
    """
    Manages semantic search over verified NCERT Class 10 Science Chapter 1 text.
    Uses NVIDIA Nemotron-3-Embed-1B (2048-dim) and Supabase pgvector (<=> cosine distance).
    """

    DEFAULT_MODEL = "nvidia/nemotron-3-embed-1b"
    EMBEDDINGS_URL = "https://integrate.api.nvidia.com/v1/embeddings"

    def __init__(
        self,
        remediation_repo: RemediationRepository,
        api_key: Optional[str] = None,
        model: Optional[str] = None
    ):
        self.remediation_repo = remediation_repo
        self.api_key = api_key or os.getenv("NVIDIA_API_KEY")
        self.model = model or os.getenv("EMBEDDING_MODEL") or self.DEFAULT_MODEL
        self.db_url = os.getenv("SUPABASE_DB_URL")

    def generate_embedding(self, text: str, input_type: str = "passage") -> Optional[List[float]]:
        """Generates real 2048-dim vector embedding via NVIDIA API."""
        if not self.api_key or len(self.api_key) < 10:
            return None

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "input": [text],
            "model": self.model,
            "input_type": input_type
        }
        try:
            resp = requests.post(self.EMBEDDINGS_URL, headers=headers, json=payload, timeout=20)
            if resp.status_code == 200:
                data = resp.json()
                return data["data"][0]["embedding"]
        except Exception:
            pass
        return None

    def search_ncert_context(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """
        Retrieves relevant NCERT textbook sections.
        Attempts Supabase pgvector similarity first; gracefully falls back to local lexical matching.
        """
        # 1. Try Vector Search via Supabase pgvector if live
        query_emb = self.generate_embedding(query, input_type="query")

        if query_emb and self.db_url:
            try:
                conn = psycopg2.connect(self.db_url, connect_timeout=4)
                cur = conn.cursor()
                # pgvector cosine distance: <=>
                vector_str = "[" + ",".join(str(x) for x in query_emb) + "]"
                cur.execute(
                    """
                    SELECT chunk_id, section_heading, page_number, chunk_text,
                           1 - (embedding <=> %s::vector) AS similarity
                    FROM curriculum_embeddings
                    WHERE embedding IS NOT NULL
                    ORDER BY embedding <=> %s::vector
                    LIMIT %s;
                    """,
                    (vector_str, vector_str, top_k)
                )
                rows = cur.fetchall()
                cur.close()
                conn.close()

                if rows:
                    return [
                        {
                            "chunk_id": r[0],
                            "section_heading": r[1],
                            "page_number": r[2],
                            "chunk_text": r[3],
                            "similarity_score": round(float(r[4]), 4),
                            "retrieval_method": "SUPABASE_PGVECTOR_COSINE"
                        }
                        for r in rows
                    ]
            except Exception:
                pass

        # 2. Local Fallback: Lexical TF-IDF / Token Overlap Search
        chunks = self.remediation_repo.get_chunks_by_chapter("CH-01")
        if not chunks:
            return []

        query_tokens = set(query.lower().split())
        scored = []

        for ch in chunks:
            text_tokens = ch["chunk_text"].lower().split()
            overlap = sum(1 for t in query_tokens if t in text_tokens)
            score = overlap / max(1, math.sqrt(len(text_tokens)))
            scored.append((score, ch))

        scored.sort(key=lambda x: x[0], reverse=True)
        results = []
        for score, ch in scored[:top_k]:
            results.append({
                "chunk_id": ch["chunk_id"],
                "section_heading": ch["section_heading"],
                "page_number": ch["page_number"],
                "chunk_text": ch["chunk_text"],
                "similarity_score": round(float(score), 4),
                "retrieval_method": "LOCAL_TOKEN_SIMILARITY_FALLBACK"
            })
        return results
