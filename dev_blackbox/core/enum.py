from enum import Enum


class PlatformEnum(str, Enum):
    GITHUB = "GITHUB"
    JIRA = "JIRA"
    CONFLUENCE = "CONFLUENCE"
    SLACK = "SLACK"
    USER_CONTENT = "USER_CONTENT"

    @classmethod
    def all(cls) -> list[PlatformEnum]:
        return [member for member in cls]

    @classmethod
    def platforms(cls) -> list[PlatformEnum]:
        return [member for member in cls if member != PlatformEnum.USER_CONTENT]
