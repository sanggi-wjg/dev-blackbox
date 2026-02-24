from typing import Any


class ServiceException(Exception):

    def __init__(self, message: str = "Service error occurred"):
        self.message = message
        super().__init__(self.message)


class EntityNotFoundException(ServiceException):

    def __init__(self, entity_name: str, identifier: Any):
        self.entity_name = entity_name
        self.identifier = identifier
        super().__init__(f"{entity_name} not found by {identifier}")


###############################
# NotFoundException
###############################
class UserNotFoundException(EntityNotFoundException):

    def __init__(self, identifier: Any):
        super().__init__(entity_name="User", identifier=identifier)


class GitHubUserSecretNotFoundException(EntityNotFoundException):

    def __init__(self, identifier: Any):
        super().__init__(entity_name="GitHubUserSecret", identifier=identifier)


class JiraUserNotFoundException(EntityNotFoundException):

    def __init__(self, identifier: Any):
        super().__init__(entity_name="JiraUser", identifier=identifier)


###############################
class GitHubUserSecretAlreadyExistException(ServiceException):

    def __init__(self, user_id: int):
        super().__init__(f"GitHubUserSecret already exists. (UserId: {user_id})")


class GitHubUserSecretNotSetException(ServiceException):

    def __init__(self, user_id: int):
        super().__init__(
            f"Set GitHub personal access token before executing events. (UserId: {user_id})"
        )


class JiraUserNotAssignedException(ServiceException):

    def __init__(self, user_id: int):
        super().__init__(f"JiraUser not assigned to User. (UserId: {user_id}")


class JiraUserProjectNotAssignedException(ServiceException):

    def __init__(self, user_id: int):
        super().__init__(f"JiraUser project not assigned to User. (UserId: {user_id}")


class SlackUserByIdNotFoundException(EntityNotFoundException):

    def __init__(self, slack_user_id: int):
        super().__init__(entity_name="SlackUser", identifier=slack_user_id)


class SlackUserNotAssignedException(ServiceException):

    def __init__(self, user_id: int):
        super().__init__(f"SlackUser not assigned to User. (UserId: {user_id})")


#######################


class IdempotentRequestException(ServiceException):

    def __init__(self, idempotency_key: str):
        self.idempotency_key = idempotency_key
        super().__init__(f"Duplicate request. (Idempotency-Key: {idempotency_key})")


class ConflictRequestException(IdempotentRequestException):

    def __init__(self, idempotency_key: str):
        super().__init__(idempotency_key)


class CompletedRequestException(IdempotentRequestException):

    def __init__(self, idempotency_key: str, cached_response: dict):
        self.cached_response = cached_response
        super().__init__(idempotency_key)


class SlackClientException(ServiceException):

    def __init__(self, message: str = "Slack API error occurred"):
        super().__init__(message)


class NoSlackChannelsFound(ServiceException):

    def __init__(self):
        super().__init__(f"No channels found invite slack bot first.")
