import os
from openai import OpenAI
from app.models import get_db
from app.services.embeddings import get_embedding
from dotenv import load_dotenv

load_dotenv()

def get_client():
    return OpenAI(
        api_key=os.getenv("OPENAI_API_KEY"),
        base_url="https://openrouter.ai/api/v1"
    )

def find_relevant_chunks(question: str, session_id: str, limit: int = 3) -> list[str]:
    question_embedding = get_embedding(question)
    vector_str = "[" + ",".join(str(x) for x in question_embedding) + "]"

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT c.content
        FROM chunks c
        JOIN documents d ON c.document_id = d.id
        WHERE d.session_id = %s
        ORDER BY c.embedding <=> %s::vector
        LIMIT %s
    """, (session_id, vector_str, limit))

    rows = cur.fetchall()
    cur.close()
    conn.close()

    return [row[0] for row in rows]

def answer_question(question: str, session_id: str) -> str:
    client = get_client()
    relevant_chunks = find_relevant_chunks(question, session_id)

    if not relevant_chunks:
        return "I couldn't find relevant information in this document."

    context = "\n\n".join(relevant_chunks)

    prompt = f"""You are an assistant that answers questions based only on the provided document context.
If the answer is not in the context, say "I couldn't find relevant information in this document."

Context:
{context}

Question: {question}

Answer:"""

    response = client.chat.completions.create(
        model="openai/gpt-4o",
        max_tokens=1000,
        messages=[{"role": "user", "content": prompt}]
    )

    return response.choices[0].message.content
