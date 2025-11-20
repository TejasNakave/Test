import httpx
import logging
from typing import List, Dict, Any, Optional
from ..config import settings
from ..schemas import RerankResult
import time
import json

logger = logging.getLogger(__name__)

class RerankerService:
    """Service for re-ranking retrieved chunks using LLM or cross-encoder"""
    
    def __init__(self):
        self.llm_api_key = settings.LLM_API_KEY
        self.llm_base_url = settings.LLM_BASE_URL
        self.llm_model = settings.LLM_MODEL
        self.top_k_rerank = settings.TOP_K_RERANK
        self.client = None
    
    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client"""
        if not self.client:
            self.client = httpx.AsyncClient(timeout=30.0)
        return self.client
    
    async def rerank(
        self,
        query: str,
        chunks: List[Dict[str, Any]],
        top_k: Optional[int] = None
    ) -> RerankResult:
        """
        Re-rank retrieved chunks based on relevance to query
        
        Args:
            query: User question/query
            chunks: List of retrieved chunks to rerank
            top_k: Number of top chunks to return after reranking
            
        Returns:
            RerankResult with reranked chunks and scores
        """
        start_time = time.time()
        rerank_top_k = top_k or self.top_k_rerank
        
        if not chunks:
            return RerankResult(
                reranked_chunks=[],
                rerank_time_ms=0,
                scores=[]
            )
        
        try:
            logger.info(f"Re-ranking {len(chunks)} chunks, returning top {rerank_top_k}")
            
            # If we have fewer chunks than requested, return all
            if len(chunks) <= rerank_top_k:
                return RerankResult(
                    reranked_chunks=chunks,
                    rerank_time_ms=int((time.time() - start_time) * 1000),
                    scores=[chunk.get("score", 0.0) for chunk in chunks]
                )
            
            # Use LLM-based reranking if API key is available
            if self.llm_api_key:
                result = await self._rerank_with_llm(query, chunks, rerank_top_k)
            else:
                # Fallback to simple score-based reranking
                result = await self._rerank_by_score(chunks, rerank_top_k)
            
            result.rerank_time_ms = int((time.time() - start_time) * 1000)
            logger.info(f"Re-ranking completed in {result.rerank_time_ms}ms")
            
            return result
            
        except Exception as e:
            logger.error(f"Error during reranking: {str(e)}")
            # Fallback to score-based ranking
            return await self._rerank_by_score(chunks, rerank_top_k)
    
    async def _rerank_with_llm(
        self,
        query: str,
        chunks: List[Dict[str, Any]],
        top_k: int
    ) -> RerankResult:
        """Re-rank using LLM to assess relevance"""
        try:
            client = await self._get_client()
            
            # Prepare chunks for LLM evaluation
            chunk_texts = []
            for i, chunk in enumerate(chunks):
                content = chunk.get("content", "")[:500]  # Limit content length
                chunk_texts.append(f"[{i}] {content}")
            
            # Create reranking prompt
            prompt = self._build_reranking_prompt(query, chunk_texts, top_k)
            
            # Make LLM request
            headers = {
                "Authorization": f"Bearer {self.llm_api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": self.llm_model,
                "messages": [
                    {"role": "system", "content": "You are a helpful assistant that ranks text passages by relevance to a query."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.1,
                "max_tokens": 200
            }
            
            response = await client.post(
                f"{self.llm_base_url}/chat/completions",
                headers=headers,
                json=payload
            )
            
            if response.status_code != 200:
                logger.error(f"LLM reranking failed: {response.status_code}")
                return await self._rerank_by_score(chunks, top_k)
            
            llm_response = response.json()
            rankings_text = llm_response["choices"][0]["message"]["content"]
            
            # Parse LLM rankings
            ranked_indices = self._parse_llm_rankings(rankings_text, len(chunks))
            
            # Reorder chunks based on LLM rankings
            reranked_chunks = []
            scores = []
            
            for rank, idx in enumerate(ranked_indices[:top_k]):
                if idx < len(chunks):
                    chunk = chunks[idx].copy()
                    # Assign new score based on ranking position
                    new_score = 1.0 - (rank / len(ranked_indices))
                    chunk["rerank_score"] = new_score
                    reranked_chunks.append(chunk)
                    scores.append(new_score)
            
            return RerankResult(
                reranked_chunks=reranked_chunks,
                rerank_time_ms=0,  # Will be set by caller
                scores=scores
            )
            
        except Exception as e:
            logger.error(f"LLM reranking failed: {str(e)}")
            return await self._rerank_by_score(chunks, top_k)
    
    async def _rerank_by_score(
        self,
        chunks: List[Dict[str, Any]],
        top_k: int
    ) -> RerankResult:
        """Fallback reranking based on original similarity scores"""
        try:
            # Sort by original score (descending)
            sorted_chunks = sorted(
                chunks,
                key=lambda x: x.get("score", 0.0),
                reverse=True
            )
            
            top_chunks = sorted_chunks[:top_k]
            scores = [chunk.get("score", 0.0) for chunk in top_chunks]
            
            return RerankResult(
                reranked_chunks=top_chunks,
                rerank_time_ms=0,  # Will be set by caller
                scores=scores
            )
            
        except Exception as e:
            logger.error(f"Score-based reranking failed: {str(e)}")
            return RerankResult(
                reranked_chunks=chunks[:top_k],
                rerank_time_ms=0,
                scores=[0.5] * min(top_k, len(chunks))
            )
    
    def _build_reranking_prompt(
        self,
        query: str,
        chunk_texts: List[str],
        top_k: int
    ) -> str:
        """Build prompt for LLM-based reranking"""
        chunks_text = "\n\n".join(chunk_texts)
        
        return f"""Given the following query and text passages, rank the passages by relevance to the query.
Return only the indices of the top {top_k} most relevant passages, separated by commas.

Query: {query}

Text Passages:
{chunks_text}

Rank the top {top_k} most relevant passages by index (0, 1, 2, etc.):"""
    
    def _parse_llm_rankings(self, rankings_text: str, max_index: int) -> List[int]:
        """Parse LLM response to extract ranked indices"""
        try:
            # Extract numbers from the response
            import re
            numbers = re.findall(r'\b\d+\b', rankings_text)
            
            ranked_indices = []
            for num_str in numbers:
                idx = int(num_str)
                if 0 <= idx < max_index and idx not in ranked_indices:
                    ranked_indices.append(idx)
            
            # If we couldn't parse properly, fall back to original order
            if not ranked_indices:
                ranked_indices = list(range(max_index))
            
            return ranked_indices
            
        except Exception as e:
            logger.error(f"Error parsing LLM rankings: {str(e)}")
            return list(range(max_index))
    
    async def health_check(self) -> bool:
        """Check if reranking service is available"""
        try:
            if not self.llm_api_key:
                return True  # Score-based reranking always available
            
            client = await self._get_client()
            headers = {"Authorization": f"Bearer {self.llm_api_key}"}
            response = await client.get(f"{self.llm_base_url}/models", headers=headers)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Reranker health check failed: {str(e)}")
            return False
    
    async def close(self):
        """Clean up resources"""
        if self.client:
            await self.client.aclose()
            self.client = None