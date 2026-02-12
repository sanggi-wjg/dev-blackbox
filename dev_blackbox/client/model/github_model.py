from datetime import date
from typing import Literal
from zoneinfo import ZoneInfo

from pydantic import BaseModel

from dev_blackbox.datetime_util import get_date_from_iso_format


class GithubEvent(BaseModel):
    id: str
    type: Literal["PushEvent", "PullRequestEvent"] | str
    actor: dict
    repo: GithubRepository
    payload: dict  # 자동으로 변환까지는 필요 없을 듯
    public: bool
    created_at: str
    org: dict | None = None

    def get_created_date(self, tz_info: ZoneInfo) -> date:
        return get_date_from_iso_format(self.created_at, tz_info=tz_info)

    def is_type_push_event(self) -> bool:
        return self.type == "PushEvent"

    def is_type_pull_request_event(self) -> bool:
        return self.type == "PullRequestEvent"

    def get_push_event_payload(self) -> GithubPushEventPayload:
        if not self.is_type_push_event():
            raise ValueError("This event is not PushEvent.")

        return GithubPushEventPayload.model_validate(self.payload)

    def get_pull_request_event_payload(self) -> GithubPullRequestEventPayload:
        if not self.is_type_pull_request_event():
            raise ValueError("This event is not PullRequestEvent.")

        return GithubPullRequestEventPayload.model_validate(self.payload)


class GithubEventList(BaseModel):
    events: list[GithubEvent]


class GithubPushEventPayload(BaseModel):
    repository_id: int
    push_id: int
    ref: str
    head: str
    before: str


class GithubPullRequestEventPayload(BaseModel):
    action: str
    number: int
    pull_request: GithubPullRequest


class GithubPullRequest(BaseModel):
    id: int
    url: str
    number: int
    head: GithubPullRequestInfo
    base: GithubPullRequestInfo


class GithubPullRequestInfo(BaseModel):
    ref: str
    sha: str
    repo: GithubRepository


class GithubRepository(BaseModel):
    id: int
    name: str
    url: str


class GithubCommit(BaseModel):
    sha: str
    node_id: str
    commit: GithubCommitCommit
    url: str
    html_url: str
    comments_url: str
    stats: GithubCommitStats
    files: list[GithubCommitFile]

    @property
    def summary_text(self) -> str:
        return (
            f"commit message: {self.commit.message}\n"
            f"stats: +{self.stats.additions}/-{self.stats.deletions} ({self.stats.total} changes)"
        )

    @property
    def detail_text(self) -> str:
        detail = ""

        for f in self.files:
            detail += f"{f.status}: {f.filename} +{f.additions}/-{f.deletions}"
            if f.patch:
                detail += f"\n\n{f.patch}"

            detail += "\n\n"

        return f"{self.summary_text}\n\n{detail}"


class GithubCommitCommit(BaseModel):
    author: dict
    committer: dict
    message: str
    url: str


class GithubCommitStats(BaseModel):
    total: int
    additions: int
    deletions: int


class GithubCommitFile(BaseModel):
    sha: str
    status: str
    filename: str
    additions: int
    deletions: int
    changes: int
    blob_url: str
    raw_url: str
    patch: str | None = None
