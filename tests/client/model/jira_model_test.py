from dev_blackbox.client.model.jira_api_model import JiraStatusGroup


def test_jira_status_group():
    assert (
        JiraStatusGroup.IN_FLIGHT_AND_RESOLVED
        == JiraStatusGroup.IN_FLIGHT + JiraStatusGroup.RESOLVED
    )
