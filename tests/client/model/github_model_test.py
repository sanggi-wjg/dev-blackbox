from datetime import date
from zoneinfo import ZoneInfo

import pytest

from dev_blackbox.client.model.github_api_model import (
    GitHubActorModel,
    GitHubCreateEventPayloadModel,
    GitHubDeleteEventPayloadModel,
    GithubCommitFileModel,
    GithubCommitInfoModel,
    GithubCommitModel,
    GithubCommitStatsModel,
    GithubEventModel,
    GithubPullRequestEventPayload,
    GithubPullRequestInfoModel,
    GithubPullRequestModel,
    GithubPushEventPayloadModel,
    GithubRepositoryModel,
    _MAX_PATCH_LENGTH,
)

_ACTOR = GitHubActorModel(
    id=1,
    url="https://api.github.com/users/test",
    login="test",
    avatar_url="https://avatars.githubusercontent.com/u/1",
    gravatar_id="",
    display_login="test",
)

_REPO = GithubRepositoryModel(
    id=100,
    name="test/repo",
    url="https://api.github.com/repos/test/repo",
)

_PUSH_PAYLOAD = {
    "repository_id": 100,
    "push_id": 200,
    "ref": "refs/heads/main",
    "head": "abc123",
    "before": "def456",
}

_PR_INFO_HEAD = GithubPullRequestInfoModel(ref="feature-branch", sha="aaa111")
_PR_INFO_BASE = GithubPullRequestInfoModel(ref="main", sha="bbb222")

_PR_MODEL = GithubPullRequestModel(
    id=1,
    url="https://api.github.com/repos/test/repo/pulls/42",
    number=42,
    title="Add feature",
    body="Feature description",
    state="open",
    head=_PR_INFO_HEAD,
    base=_PR_INFO_BASE,
)

_PR_PAYLOAD = {
    "action": "opened",
    "number": 42,
    "pull_request": _PR_MODEL.model_dump(),
}

_CREATE_PAYLOAD = {
    "description": "new branch",
    "full_ref": "refs/heads/feature",
    "master_branch": "main",
    "pusher_type": "user",
    "ref": "feature",
    "ref_type": "branch",
}

_DELETE_PAYLOAD = {
    "full_ref": "refs/heads/old-branch",
    "pusher_type": "user",
    "ref": "old-branch",
    "ref_type": "branch",
}


def _make_event(event_type: str, payload: dict, created_at: str = "2026-03-06T15:30:00Z"):
    return GithubEventModel(
        id="evt1",
        actor=_ACTOR,
        repo=_REPO,
        type=event_type,
        payload=payload,
        public=True,
        created_at=created_at,
    )


# --- GithubEventModel.get_created_date ---


def test_get_created_date_UTC():
    # given
    event = _make_event("PushEvent", _PUSH_PAYLOAD, created_at="2026-03-06T23:30:00Z")
    tz = ZoneInfo("UTC")

    # when
    result = event.get_created_date(tz)

    # then
    assert result == date(2026, 3, 6)


def test_get_created_date_KST_날짜_넘김():
    # given
    event = _make_event("PushEvent", _PUSH_PAYLOAD, created_at="2026-03-06T16:00:00Z")
    tz = ZoneInfo("Asia/Seoul")

    # when
    result = event.get_created_date(tz)

    # then — UTC 16:00 → KST 다음날 01:00
    assert result == date(2026, 3, 7)


# --- GithubEventModel.typed_payload ---


def test_typed_payload_PushEvent():
    # given
    event = _make_event("PushEvent", _PUSH_PAYLOAD)

    # when
    payload = event.typed_payload

    # then
    assert isinstance(payload, GithubPushEventPayloadModel)
    assert payload.push_id == 200


def test_typed_payload_PullRequestEvent():
    # given
    event = _make_event("PullRequestEvent", _PR_PAYLOAD)

    # when
    payload = event.typed_payload

    # then
    assert isinstance(payload, GithubPullRequestEventPayload)
    assert payload.number == 42


def test_typed_payload_CreateEvent():
    # given
    event = _make_event("CreateEvent", _CREATE_PAYLOAD)

    # when
    payload = event.typed_payload

    # then
    assert isinstance(payload, GitHubCreateEventPayloadModel)
    assert payload.ref == "feature"


def test_typed_payload_DeleteEvent():
    # given
    event = _make_event("DeleteEvent", _DELETE_PAYLOAD)

    # when
    payload = event.typed_payload

    # then
    assert isinstance(payload, GitHubDeleteEventPayloadModel)
    assert payload.ref == "old-branch"


def test_typed_payload_알_수_없는_이벤트는_dict_반환():
    # given
    raw = {"custom_field": "value"}
    event = _make_event("WatchEvent", raw)

    # when
    payload = event.typed_payload

    # then
    assert isinstance(payload, dict)
    assert payload == raw


# --- push_event_payload / pull_request_event_payload ---


def test_push_event_payload_정상():
    # given
    event = _make_event("PushEvent", _PUSH_PAYLOAD)

    # when
    payload = event.push_event_payload

    # then
    assert payload.ref == "refs/heads/main"


def test_push_event_payload_타입_불일치_시_ValueError():
    # given
    event = _make_event("PullRequestEvent", _PR_PAYLOAD)

    # when & then
    with pytest.raises(ValueError, match="not PushEvent"):
        _ = event.push_event_payload


def test_pull_request_event_payload_정상():
    # given
    event = _make_event("PullRequestEvent", _PR_PAYLOAD)

    # when
    payload = event.pull_request_event_payload

    # then
    assert payload.action == "opened"


def test_pull_request_event_payload_타입_불일치_시_ValueError():
    # given
    event = _make_event("PushEvent", _PUSH_PAYLOAD)

    # when & then
    with pytest.raises(ValueError, match="not PullRequestEvent"):
        _ = event.pull_request_event_payload


# --- pull_request_summary_text ---


def test_pull_request_summary_text_body_포함():
    # given
    event = _make_event("PullRequestEvent", _PR_PAYLOAD)

    # when
    text = event.pull_request_summary_text

    # then
    assert "PR #42 (opened): Add feature" in text
    assert "main ← feature-branch" in text
    assert "Feature description" in text


def test_pull_request_summary_text_body_없는_경우():
    # given
    pr = _PR_MODEL.model_copy(update={"body": None})
    payload = {"action": "closed", "number": 42, "pull_request": pr.model_dump()}
    event = _make_event("PullRequestEvent", payload)

    # when
    text = event.pull_request_summary_text

    # then
    assert "PR #42 (closed)" in text
    assert text.count("\n") == 1  # body 줄 없음


def test_pull_request_summary_text_PushEvent이면_빈_문자열():
    # given
    event = _make_event("PushEvent", _PUSH_PAYLOAD)

    # when
    text = event.pull_request_summary_text

    # then
    assert text == ""


# --- GithubCommitModel ---


def _make_commit(files: list[GithubCommitFileModel] | None = None):
    return GithubCommitModel(
        sha="abc123",
        node_id="node1",
        commit=GithubCommitInfoModel(
            author={"name": "tester"},
            committer={"name": "tester"},
            message="fix: resolve bug",
            url="https://api.github.com/repos/test/repo/commits/abc123",
        ),
        url="https://api.github.com/repos/test/repo/commits/abc123",
        html_url="https://github.com/test/repo/commit/abc123",
        comments_url="https://api.github.com/repos/test/repo/commits/abc123/comments",
        stats=GithubCommitStatsModel(total=10, additions=7, deletions=3),
        files=files or [],
    )


def test_commit_summary_text():
    # given
    commit = _make_commit()

    # when
    text = commit.commit_summary_text

    # then
    assert "fix: resolve bug" in text
    assert "+7/-3 (10 changes)" in text


def test_commit_detail_text_파일_패치_포함():
    # given
    files = [
        GithubCommitFileModel(
            sha="f1",
            status="modified",
            filename="src/app.py",
            additions=5,
            deletions=2,
            changes=7,
            blob_url="https://blob",
            raw_url="https://raw",
            patch="@@ -1,5 +1,8 @@\n+new line",
        ),
    ]
    commit = _make_commit(files)

    # when
    text = commit.commit_detail_text

    # then
    assert "modified: src/app.py +5/-2" in text
    assert "+new line" in text
    assert "truncated" not in text


def test_commit_detail_text_패치가_긴_경우_잘림():
    # given
    long_patch = "x" * (_MAX_PATCH_LENGTH + 100)
    files = [
        GithubCommitFileModel(
            sha="f2",
            status="added",
            filename="big_file.py",
            additions=100,
            deletions=0,
            changes=100,
            blob_url="https://blob",
            raw_url="https://raw",
            patch=long_patch,
        ),
    ]
    commit = _make_commit(files)

    # when
    text = commit.commit_detail_text

    # then
    assert "... (truncated)" in text


def test_commit_detail_text_패치_없는_파일():
    # given
    files = [
        GithubCommitFileModel(
            sha="f3",
            status="removed",
            filename="old.py",
            additions=0,
            deletions=10,
            changes=10,
            blob_url="https://blob",
            raw_url="https://raw",
            patch=None,
        ),
    ]
    commit = _make_commit(files)

    # when
    text = commit.commit_detail_text

    # then
    assert "removed: old.py +0/-10" in text
    assert "truncated" not in text
