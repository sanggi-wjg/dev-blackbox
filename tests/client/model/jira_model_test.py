from datetime import date
from zoneinfo import ZoneInfo

from dev_blackbox.client.model.jira_api_model import (
    IssueJQL,
    JiraChangelogHistoryModel,
    JiraChangelogItemModel,
    JiraCommentModel,
    JiraIssueModel,
    JiraIssueStatus,
    JiraStatusGroup,
)

KST = ZoneInfo("Asia/Seoul")


# --- JiraStatusGroup ---


def test_jira_status_group_IN_FLIGHT_AND_RESOLVED은_IN_FLIGHT와_RESOLVED의_합():
    # given & when & then
    assert (
        JiraStatusGroup.IN_FLIGHT_AND_RESOLVED
        == JiraStatusGroup.IN_FLIGHT + JiraStatusGroup.RESOLVED
    )


def test_jira_status_group_ALL은_11개():
    # given & when & then
    assert len(JiraStatusGroup.ALL) == 11


def test_jira_status_group_IN_FLIGHT는_ALL의_부분집합():
    # given & when & then
    assert all(s in JiraStatusGroup.ALL for s in JiraStatusGroup.IN_FLIGHT)


# --- IssueJQL.build ---


def test_jql_빈_조건이면_ORDER_BY만():
    # given
    jql = IssueJQL()

    # when
    result = jql.build()

    # then
    assert result == " ORDER BY updatedDate DESC"


def test_jql_project_조건():
    # given
    jql = IssueJQL(project="FMP", order_by=None)

    # when
    result = jql.build()

    # then
    assert result == "project = 'FMP'"


def test_jql_assignee_조건():
    # given
    jql = IssueJQL(assignee_account_id="acc123", order_by=None)

    # when
    result = jql.build()

    # then
    assert result == "assignee = 'acc123'"


def test_jql_include_status_단일():
    # given
    jql = IssueJQL(include_status=JiraIssueStatus.IN_PROGRESS, order_by=None)

    # when
    result = jql.build()

    # then
    assert result == "status = 'In Progress'"


def test_jql_include_statuses_복수():
    # given
    jql = IssueJQL(include_statuses=[JiraIssueStatus.DONE, JiraIssueStatus.CLOSED], order_by=None)

    # when
    result = jql.build()

    # then
    assert result == "status in ('Done', 'Closed')"


def test_jql_updated_within():
    # given
    jql = IssueJQL(updated_within="-1d", order_by=None)

    # when
    result = jql.build()

    # then
    assert result == "updatedDate >= -1d"


def test_jql_updated_after_before():
    # given
    jql = IssueJQL(updated_after="2026-03-06", updated_before="2026-03-07", order_by=None)

    # when
    result = jql.build()

    # then
    assert "updatedDate >= '2026-03-06'" in result
    assert "updatedDate < '2026-03-07'" in result
    assert " AND " in result


def test_jql_모든_조건_조합():
    # given
    jql = IssueJQL(
        project="FMP",
        assignee_account_id="acc1",
        include_status=JiraIssueStatus.IN_PROGRESS,
        updated_after="2026-03-06",
    )

    # when
    result = jql.build()

    # then
    assert "project = 'FMP'" in result
    assert "assignee = 'acc1'" in result
    assert "status = 'In Progress'" in result
    assert "updatedDate >= '2026-03-06'" in result
    assert "ORDER BY updatedDate DESC" in result


# --- JiraChangelogHistoryModel.get_created_date ---


def test_changelog_get_created_date_KST():
    # given
    history = JiraChangelogHistoryModel(
        id="1",
        created="2026-03-06T16:00:00.000+0000",
        items=[],
    )

    # when — UTC 16:00 → KST 다음날 01:00
    result = history.get_created_date(KST)

    # then
    assert result == date(2026, 3, 7)


# --- JiraCommentModel.get_created_date ---


def test_comment_get_created_date_KST():
    # given
    comment = JiraCommentModel(
        author_display_name="tester",
        body="test comment",
        created="2026-03-06T14:00:00.000+0000",
    )

    # when — UTC 14:00 → KST 23:00 (같은 날)
    result = comment.get_created_date(KST)

    # then
    assert result == date(2026, 3, 6)


# --- JiraIssueModel.from_raw ---


def test_from_raw_전체_필드():
    # given
    raw = {
        "id": "10001",
        "key": "FMP-123",
        "fields": {
            "summary": "Fix login bug",
            "status": {"name": "In Progress"},
            "issuetype": {"name": "Bug"},
            "priority": {"name": "High"},
            "assignee": {"displayName": "홍길동"},
            "comment": {
                "comments": [
                    {
                        "author": {"displayName": "작성자"},
                        "body": "코멘트 내용",
                        "created": "2026-03-06T10:00:00.000+0000",
                    }
                ]
            },
        },
        "changelog": {
            "histories": [
                {
                    "id": "h1",
                    "created": "2026-03-06T09:00:00.000+0000",
                    "items": [{"field": "status", "fromString": "Open", "toString": "In Progress"}],
                }
            ]
        },
    }

    # when
    issue = JiraIssueModel.from_raw(raw)

    # then
    assert issue.id == "10001"
    assert issue.key == "FMP-123"
    assert issue.summary == "Fix login bug"
    assert issue.status == "In Progress"
    assert issue.issue_type == "Bug"
    assert issue.priority == "High"
    assert issue.assignee_display_name == "홍길동"
    assert len(issue.comments) == 1
    assert issue.comments[0].body == "코멘트 내용"
    assert len(issue.changelog_histories) == 1
    assert issue.changelog_histories[0].items[0].to_string == "In Progress"


def test_from_raw_최소_필드():
    # given
    raw = {}

    # when
    issue = JiraIssueModel.from_raw(raw)

    # then
    assert issue.id == ""
    assert issue.key == ""
    assert issue.summary == ""
    assert issue.status == ""
    assert issue.issue_type == ""
    assert issue.priority is None
    assert issue.assignee_display_name is None
    assert issue.comments == []
    assert issue.changelog_histories == []


def test_from_raw_null_필드():
    # given — status, issuetype, priority, assignee가 None
    raw = {
        "id": "10002",
        "key": "FMP-456",
        "fields": {
            "summary": "Some task",
            "status": None,
            "issuetype": None,
            "priority": None,
            "assignee": None,
            "comment": None,
        },
    }

    # when
    issue = JiraIssueModel.from_raw(raw)

    # then
    assert issue.status == ""
    assert issue.issue_type == ""
    assert issue.priority is None
    assert issue.assignee_display_name is None
    assert issue.comments == []


# --- filter_changelog_by_date / filter_comments_by_date ---


def _make_issue_with_history_and_comments():
    return JiraIssueModel(
        id="10001",
        key="FMP-100",
        summary="Test issue",
        status="Done",
        issue_type="Task",
        changelog_histories=[
            JiraChangelogHistoryModel(
                id="h1",
                created="2026-03-06T02:00:00.000+0900",  # KST 3/6
                items=[
                    JiraChangelogItemModel(
                        field="status", from_string="Open", to_string="In Progress"
                    )
                ],
            ),
            JiraChangelogHistoryModel(
                id="h2",
                created="2026-03-07T02:00:00.000+0900",  # KST 3/7
                items=[
                    JiraChangelogItemModel(
                        field="status", from_string="In Progress", to_string="Done"
                    )
                ],
            ),
        ],
        comments=[
            JiraCommentModel(
                author_display_name="tester",
                body="3월 6일 코멘트",
                created="2026-03-06T10:00:00.000+0900",
            ),
            JiraCommentModel(
                author_display_name="tester",
                body="3월 7일 코멘트",
                created="2026-03-07T10:00:00.000+0900",
            ),
        ],
    )


def test_filter_changelog_by_date_해당_날짜만_반환():
    # given
    issue = _make_issue_with_history_and_comments()
    target = date(2026, 3, 6)

    # when
    result = issue.filter_changelog_by_date(target, KST)

    # then
    assert len(result) == 1
    assert result[0].id == "h1"


def test_filter_changelog_by_date_해당_없으면_빈_리스트():
    # given
    issue = _make_issue_with_history_and_comments()
    target = date(2026, 3, 8)

    # when
    result = issue.filter_changelog_by_date(target, KST)

    # then
    assert result == []


def test_filter_comments_by_date_해당_날짜만_반환():
    # given
    issue = _make_issue_with_history_and_comments()
    target = date(2026, 3, 7)

    # when
    result = issue.filter_comments_by_date(target, KST)

    # then
    assert len(result) == 1
    assert result[0].body == "3월 7일 코멘트"


# --- _base_info_text ---


def test_base_info_text_priority와_labels_포함():
    # given
    issue = JiraIssueModel(
        id="1",
        key="FMP-1",
        summary="Task",
        status="Open",
        issue_type="Story",
        priority="High",
        labels=["backend", "urgent"],
    )

    # when
    text = issue._base_info_text

    # then
    assert "[FMP-1] Story: Task" in text
    assert "현재 상태: Open" in text
    assert "우선순위: High" in text
    assert "라벨: backend, urgent" in text


def test_base_info_text_priority와_labels_없는_경우():
    # given
    issue = JiraIssueModel(
        id="2",
        key="FMP-2",
        summary="Simple",
        status="Done",
        issue_type="Bug",
    )

    # when
    text = issue._base_info_text

    # then
    assert "우선순위" not in text
    assert "라벨" not in text


# --- issue_detail_text ---


def test_issue_detail_text_changelog과_comment_포함():
    # given
    issue = _make_issue_with_history_and_comments()
    target = date(2026, 3, 6)

    # when
    text = issue.issue_detail_text(target, KST)

    # then
    assert "[FMP-100] Task: Test issue" in text
    assert "변경 이력:" in text
    assert "상태: Open → In Progress" in text
    assert "코멘트:" in text
    assert "3월 6일 코멘트" in text
    # 3/7 데이터는 포함되지 않아야 함
    assert "Done" not in text.split("변경 이력:")[1].split("코멘트:")[0]
    assert "3월 7일 코멘트" not in text


def test_issue_detail_text_changelog과_comment_없는_날짜():
    # given
    issue = _make_issue_with_history_and_comments()
    target = date(2026, 3, 8)

    # when
    text = issue.issue_detail_text(target, KST)

    # then
    assert "변경 이력:" not in text
    assert "코멘트:" not in text


def test_issue_detail_text_긴_코멘트는_500자로_잘림():
    # given
    long_body = "가" * 600
    issue = JiraIssueModel(
        id="1",
        key="FMP-1",
        summary="Task",
        status="Open",
        issue_type="Task",
        comments=[
            JiraCommentModel(
                author_display_name="tester",
                body=long_body,
                created="2026-03-06T10:00:00.000+0900",
            ),
        ],
    )
    target = date(2026, 3, 6)

    # when
    text = issue.issue_detail_text(target, KST)

    # then — 코멘트 본문이 500자로 잘림
    comment_section = text.split("코멘트:")[1]
    # 원본 600자가 아닌 500자만 포함
    assert "가" * 500 in comment_section
    assert "가" * 501 not in comment_section
