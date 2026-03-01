import uuid

from dev_blackbox.client.model.github_api_model import (
    GithubEventModel,
    GithubRepositoryModel,
    GitHubActorModel,
)


def create_github_event_model(
    event_id: str,
    event_type: str = "PushEvent",
) -> GithubEventModel:
    return GithubEventModel(
        id=event_id,
        type=event_type,
        actor=GitHubActorModel(
            id=1,
            url="https://api.github.com/users/test",
            login="test",
            avatar_url="https://avatars.githubusercontent.com/u/12345678?v=4",
            gravatar_id="abc123",
            display_login="Test",
        ),
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
