import uuid

from dev_blackbox.client.model.github_api_model import (
    GithubCommitFileModel,
    GithubCommitInfoModel,
    GithubCommitModel,
    GithubCommitStatsModel,
    GithubEventModel,
    GithubRepositoryModel,
    GitHubActorModel,
)


def create_github_commit_model(
    sha: str = "abc123",
    message: str = "fix: resolve login bug",
) -> GithubCommitModel:
    return GithubCommitModel(
        sha=sha,
        node_id="MDY6Q29tbWl0MTIzNDU2Nzg5",
        commit=GithubCommitInfoModel(
            author={"name": "test", "email": "test@example.com", "date": "2025-01-01T00:00:00Z"},
            committer={
                "name": "test",
                "email": "test@example.com",
                "date": "2025-01-01T00:00:00Z",
            },
            message=message,
            url=f"https://api.github.com/repos/test/repo/git/commits/{sha}",
        ),
        url=f"https://api.github.com/repos/test/repo/commits/{sha}",
        html_url=f"https://github.com/test/repo/commit/{sha}",
        comments_url=f"https://api.github.com/repos/test/repo/commits/{sha}/comments",
        stats=GithubCommitStatsModel(total=10, additions=7, deletions=3),
        files=[
            GithubCommitFileModel(
                sha="file_sha_1",
                status="modified",
                filename="src/main.py",
                additions=5,
                deletions=2,
                changes=7,
                blob_url=f"https://github.com/test/repo/blob/{sha}/src/main.py",
                raw_url=f"https://github.com/test/repo/raw/{sha}/src/main.py",
                patch="@@ -1,5 +1,8 @@\n+import os\n",
            ),
        ],
    )


def create_github_event_model(
    event_id: str,
    event_type: str = "PushEvent",
    created_at: str = "2025-01-01T00:00:00Z",
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
        created_at=created_at,
    )
