from sqlalchemy.orm import Session

from dev_blackbox.agent.embedding_agent import get_embedding_agent
from dev_blackbox.service.query.search_query import SearchQuery
from dev_blackbox.storage.rds.projection.platform_work_log_projection import (
    PlatformWorkLogWithDistanceProjection,
)
from dev_blackbox.storage.rds.repository import PlatformWorkLogRepository


class SearchService:

    def __init__(self, session: Session):
        self.platform_work_log_repository = PlatformWorkLogRepository(session)

    def search_platform_work_logs(
        self,
        query: SearchQuery,
    ) -> list[PlatformWorkLogWithDistanceProjection]:
        embedding_agent = get_embedding_agent()
        query_embedding = embedding_agent.get_embedding(query.query_text)
        return self.platform_work_log_repository.find_similar_by_embedding(
            user_id=query.user_id,
            query_embedding=query_embedding,
            limit=query.limit,
        )
