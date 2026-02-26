from typing import NamedTuple

from dev_blackbox.storage.rds.entity.github_event import GitHubEvent
from dev_blackbox.storage.rds.entity.jira_event import JiraEvent
from dev_blackbox.storage.rds.entity.platform_work_log import PlatformWorkLog
from dev_blackbox.storage.rds.entity.slack_message import SlackMessage


class PlatformWorkLogsWithSources(NamedTuple):
    work_logs: list[PlatformWorkLog]
    github_events: list[GitHubEvent]
    jira_events: list[JiraEvent]
    slack_messages: list[SlackMessage]
