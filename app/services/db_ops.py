async def insert_job_embedding(title: str, desc: str):
    emb = embed_text(desc)
    await supabase.table("job_embeddings").insert({
        "title": title,
        "description": desc,
        "embedding": emb
    }).execute()
