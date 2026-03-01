from datetime import date
from functools import cached_property
from typing import Literal
from zoneinfo import ZoneInfo

from pydantic import BaseModel

from dev_blackbox.util.datetime_util import get_date_from_iso_format


class GithubEventModel(BaseModel):
    id: str
    actor: GitHubActorModel
    repo: GithubRepositoryModel
    type: Literal["PushEvent", "PullRequestEvent", "CreateEvent", "DeleteEvent"] | str
    payload: GithubPushEventPayloadModel | GithubPullRequestEventPayload | dict
    public: bool
    created_at: str
    org: dict | None = None

    def get_created_date(self, tz_info: ZoneInfo) -> date:
        return get_date_from_iso_format(self.created_at, tz_info=tz_info)

    @cached_property
    def typed_payload(self) -> GithubPushEventPayloadModel | GithubPullRequestEventPayload | dict:
        match self.type:
            case "PushEvent":
                return GithubPushEventPayloadModel.model_validate(self.payload)
            case "PullRequestEvent":
                return GithubPullRequestEventPayload.model_validate(self.payload)
            case _:
                return self.payload

    @property
    def push_event_payload(self) -> GithubPushEventPayloadModel:
        if not isinstance(self.typed_payload, GithubPushEventPayloadModel):
            raise ValueError("This event is not PushEvent.")
        return self.typed_payload

    @property
    def pull_request_event_payload(self) -> GithubPullRequestEventPayload:
        if not isinstance(self.typed_payload, GithubPullRequestEventPayload):
            raise ValueError("This event is not PullRequestEvent.")
        return self.typed_payload

    @cached_property
    def pull_request_summary_text(self) -> str:
        if self.type != "PullRequestEvent":
            return ""

        payload = self.pull_request_event_payload
        pr = payload.pull_request
        lines = [
            f"PR #{payload.number} ({payload.action}): {pr.title}",
            f"{pr.base.ref} ← {pr.head.ref}",
        ]
        if pr.body:
            lines.append(pr.body)
        return "\n".join(lines)


class GithubEventModelList(BaseModel):
    events: list[GithubEventModel]


class GitHubActorModel(BaseModel):
    id: int
    url: str
    login: str
    avatar_url: str
    gravatar_id: str
    display_login: str


class GithubPushEventPayloadModel(BaseModel):
    repository_id: int
    push_id: int
    ref: str
    head: str
    before: str


class GithubRepositoryModel(BaseModel):
    id: int
    name: str
    url: str


class GithubPullRequestInfoModel(BaseModel):
    ref: str
    sha: str
    repo: GithubRepositoryModel | None = None  # fork 삭제 시 null


class GithubPullRequestModel(BaseModel):
    id: int
    url: str
    number: int
    html_url: str | None = None
    title: str | None = None
    body: str | None = None
    state: str | None = None  # "open" | "closed"
    draft: bool | None = None
    merged: bool | None = None
    head: GithubPullRequestInfoModel
    base: GithubPullRequestInfoModel


class GithubPullRequestEventPayload(BaseModel):
    action: str
    number: int
    pull_request: GithubPullRequestModel


class GithubCommitInfoModel(BaseModel):
    author: dict
    committer: dict
    message: str
    url: str


class GithubCommitStatsModel(BaseModel):
    total: int
    additions: int
    deletions: int


class GithubCommitFileModel(BaseModel):
    sha: str
    status: str
    filename: str
    additions: int
    deletions: int
    changes: int
    blob_url: str
    raw_url: str
    patch: str | None = None


_MAX_PATCH_LENGTH = 500


class GithubCommitModel(BaseModel):
    sha: str
    node_id: str
    commit: GithubCommitInfoModel
    url: str
    html_url: str
    comments_url: str
    stats: GithubCommitStatsModel
    files: list[GithubCommitFileModel]

    @cached_property
    def commit_summary_text(self) -> str:
        return (
            f"commit message: {self.commit.message}\n"
            f"stats: +{self.stats.additions}/-{self.stats.deletions} ({self.stats.total} changes)"
        )

    @cached_property
    def commit_detail_text(self) -> str:
        detail = ""

        for f in self.files:
            detail += f"{f.status}: {f.filename} +{f.additions}/-{f.deletions}"
            if f.patch:
                patch = f.patch[:_MAX_PATCH_LENGTH]
                if len(f.patch) > _MAX_PATCH_LENGTH:
                    patch += "\n... (truncated)"
                detail += f"\n\n{patch}"

            detail += "\n\n"

        return f"{self.commit_summary_text}\n\n{detail}"
