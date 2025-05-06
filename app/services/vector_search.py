# app/services/vector_search.py

from typing import List
from app.services.embeddings import embed_text
from app.services.db_client import get_pg_connection 
import asyncpg

async def insert_job_embedding(title: str, description: str):
    embedding = embed_text(description)
    conn = await get_pg_connection()
    await conn.execute(
        """
        INSERT INTO job_embeddings (title, description, embedding)
        VALUES ($1, $2, $3)
        """, title, description, embedding
    )
    await conn.close()

async def find_similar_jobs(query: str, top_k: int = 3) -> List[dict]:
    embedding = embed_text(query)
    conn = await get_pg_connection()
    rows = await conn.fetch(
        """
        SELECT title, description
        FROM job_embeddings
        ORDER BY embedding <#> $1
        LIMIT $2
        """, embedding, top_k
    )
    await conn.close()
    return [dict(r) for r in rows]
