"""
Embedding service for duplicate detection using OpenAI
"""
from typing import List, Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
import structlog
import openai
from openai import AsyncOpenAI

from app.models import Embedding, Idea
from app.core.config import settings

logger = structlog.get_logger(__name__)


class EmbeddingService:
    """Service for generating and searching embeddings"""

    def __init__(self):
        if settings.OPENAI_API_KEY:
            self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        else:
            self.client = None
            logger.warning("OpenAI API key not configured, embeddings disabled")

    async def generate_embedding(
        self,
        db: AsyncSession,
        entity_id: int,
        entity_type: str,
        text: str
    ) -> Optional[int]:
        """Generate embedding for text and store it"""
        if not self.client:
            return None

        try:
            # Generate embedding using OpenAI
            response = await self.client.embeddings.create(
                input=text,
                model=settings.OPENAI_EMBEDDING_MODEL
            )

            embedding_vector = response.data[0].embedding

            # Store embedding in database
            embedding = Embedding(
                entity_type=entity_type,
                entity_id=entity_id,
                vector=embedding_vector,
                model=settings.OPENAI_EMBEDDING_MODEL,
                text_content=text
            )

            db.add(embedding)
            await db.commit()
            await db.refresh(embedding)

            logger.info(
                "Generated embedding",
                entity_type=entity_type,
                entity_id=entity_id,
                model=settings.OPENAI_EMBEDDING_MODEL
            )

            return embedding.id

        except Exception as e:
            logger.error("Failed to generate embedding", error=str(e))
            return None

    async def find_duplicates(
        self,
        db: AsyncSession,
        idea_id: int,
        threshold: float = None
    ) -> List[Dict]:
        """Find similar ideas using vector similarity search"""
        if not self.client:
            return []

        threshold = threshold or settings.DUPLICATE_SIMILARITY_THRESHOLD

        try:
            # Get the embedding for the idea
            query = select(Embedding).where(
                Embedding.entity_type == "idea",
                Embedding.entity_id == idea_id
            )
            result = await db.execute(query)
            target_embedding = result.scalar_one_or_none()

            if not target_embedding:
                return []

            # Use pgvector for similarity search
            similarity_query = text("""
                SELECT
                    e.entity_id as idea_id,
                    i.title,
                    i.status,
                    1 - (e.vector <=> :target_vector) as similarity_score
                FROM embeddings e
                JOIN ideas i ON e.entity_id = i.id
                WHERE e.entity_type = 'idea'
                  AND e.entity_id != :idea_id
                  AND 1 - (e.vector <=> :target_vector) > :threshold
                ORDER BY similarity_score DESC
                LIMIT 5
            """)

            result = await db.execute(similarity_query, {
                "target_vector": target_embedding.vector,
                "idea_id": idea_id,
                "threshold": threshold
            })

            duplicates = []
            for row in result:
                duplicates.append({
                    "idea_id": row.idea_id,
                    "title": row.title,
                    "similarity_score": float(row.similarity_score),
                    "status": row.status
                })

            logger.info(
                "Found potential duplicates",
                idea_id=idea_id,
                duplicate_count=len(duplicates)
            )

            return duplicates

        except Exception as e:
            logger.error("Failed to find duplicates", error=str(e))
            return []

    async def search_similar(
        self,
        db: AsyncSession,
        query_text: str,
        limit: int = 10
    ) -> List[Dict]:
        """Search for ideas similar to query text"""
        if not self.client:
            return []

        try:
            # Generate embedding for query
            response = await self.client.embeddings.create(
                input=query_text,
                model=settings.OPENAI_EMBEDDING_MODEL
            )

            query_vector = response.data[0].embedding

            # Search for similar ideas
            similarity_query = text("""
                SELECT
                    e.entity_id as idea_id,
                    i.title,
                    i.raw_input,
                    i.status,
                    1 - (e.vector <=> :query_vector) as similarity_score
                FROM embeddings e
                JOIN ideas i ON e.entity_id = i.id
                WHERE e.entity_type = 'idea'
                  AND 1 - (e.vector <=> :query_vector) > 0.1
                ORDER BY similarity_score DESC
                LIMIT :limit
            """)

            result = await db.execute(similarity_query, {
                "query_vector": query_vector,
                "limit": limit
            })

            results = []
            for row in result:
                results.append({
                    "idea_id": row.idea_id,
                    "title": row.title,
                    "raw_input": row.raw_input,
                    "similarity_score": float(row.similarity_score),
                    "status": row.status
                })

            return results

        except Exception as e:
            logger.error("Failed to search similar ideas", error=str(e))
            return []
