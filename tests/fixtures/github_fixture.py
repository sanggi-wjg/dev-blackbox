import uuid

from dev_blackbox.client.model.github_api_model import GithubEventModel, GithubRepositoryModel


def create_github_event_model(
    event_id: str,
    event_type: str = "PushEvent",
) -> GithubEventModel:
    return GithubEventModel(
        id=event_id,
        type=event_type,
        actor={},
        repo=GithubRepositoryModel(
            id=1, name="test/repo", url="https://api.github.com/repos/test/repo"
        ),
        payload={
            "repository_id": 1,
            "push_id": 1,
            "ref": "refs/heads/main",
            "head": "abc123",
            "before": "def456",
        },
        public=True,
        created_at="2025-01-01T00:00:00Z",
    )
