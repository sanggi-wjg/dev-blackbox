def create_jira_issue_raw(
    issue_id: str = "10001",
    key: str = "PROJ-1",
    summary: str = "Test Issue",
    status: str = "In Progress",
    issue_type: str = "Task",
    priority: str = "Medium",
    changelog_histories: list[dict] | None = None,
) -> dict:
    """Jira REST API의 Issue.raw 형태를 생성한다."""
    return {
        "id": issue_id,
        "key": key,
        "fields": {
            "summary": summary,
            "status": {"name": status},
            "issuetype": {"name": issue_type},
            "priority": {"name": priority},
            "assignee": {"displayName": "Test User"},
            "comment": {"comments": []},
        },
        "changelog": {
            "histories": changelog_histories or [],
        },
    }
