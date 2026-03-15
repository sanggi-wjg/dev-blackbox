from sqlalchemy.orm import Session

from dev_blackbox.agent.embedding_agent import get_embedding_agent
from dev_blackbox.service.model.search_model import PlatformWorkLogSearchResult
from dev_blackbox.service.query.search_query import SearchQuery
from dev_blackbox.storage.rds.repository import (
    PlatformWorkLogChunkRepository,
    PlatformWorkLogRepository,
)


class SearchService:

    def __init__(self, session: Session):
        self.platform_work_log_repository = PlatformWorkLogRepository(session)
        self.platform_work_log_chunk_repository = PlatformWorkLogChunkRepository(session)

    def search_platform_work_logs(
        self,
        query: SearchQuery,
    ) -> list[PlatformWorkLogSearchResult]:
        embedding_agent = get_embedding_agent()
        query_embedding = embedding_agent.get_embedding(query.query_text)

        chunk_results = self.platform_work_log_chunk_repository.find_similar_by_embedding(
            user_id=query.user_id,
            query_embedding=query_embedding,
            limit=query.limit * 3,  # 결과 확보를 위해서
            similarity=query.similarity,
        )
        if not chunk_results:
            return []

        # chunk로 나누어져 있어서 work_log_id 별로 min 필터링
        best_by_work_log: dict[int, float] = {}
        for result in chunk_results:
            work_log_id = result.platform_work_log_chunk.platform_work_log_id
            best_by_work_log[work_log_id] = min(
                result.distance, best_by_work_log.get(work_log_id, float("inf"))
            )

        # distance 순 정렬 후 limit 적용
        sorted_entries = sorted(best_by_work_log.items(), key=lambda x: x[1])[: query.limit]
        if not sorted_entries:
            return []

        work_log_ids = [entry[0] for entry in sorted_entries]
        work_logs = self.platform_work_log_repository.find_all_by_id(work_log_ids)
        work_log_map = {wl.id: wl for wl in work_logs}

        return [
            PlatformWorkLogSearchResult(
                platform_work_log=work_log_map[work_log_id],
                distance=distance,
            )
            for work_log_id, distance in sorted_entries
            if work_log_id in work_log_map
        ]
