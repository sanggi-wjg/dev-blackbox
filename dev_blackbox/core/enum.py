from enum import StrEnum


class PlatformEnum(StrEnum):
    GITHUB = "GITHUB"
    JIRA = "JIRA"
    CONFLUENCE = "CONFLUENCE"
    SLACK = "SLACK"
    USER_CONTENT = "USER_CONTENT"

    @classmethod
    def platforms(cls) -> list[PlatformEnum]:
        return [member for member in cls if member != PlatformEnum.USER_CONTENT]


class TaskStatusEnum(StrEnum):
    BACKLOG = "BACKLOG"
    TODO = "TODO"
    IN_PROGRESS = "IN_PROGRESS"
    DONE = "DONE"
    CANCELED = "CANCELED"
