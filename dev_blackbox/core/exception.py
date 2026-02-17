class ServiceException(Exception):

    def __init__(self, message: str = "Service error occurred"):
        self.message = message
        super().__init__(self.message)


class EntityNotFoundException(ServiceException):

    def __init__(self, entity_name: str, identifier: int | str):
        self.entity_name = entity_name
        self.identifier = identifier
        super().__init__(f"{entity_name} not found by {identifier}")


###############################
# NotFoundException
###############################
class UserByIdNotFoundException(EntityNotFoundException):

    def __init__(self, user_id: int):
        super().__init__(entity_name="User", identifier=user_id)


class UserByNameNotFoundException(EntityNotFoundException):

    def __init__(self, username: str):
        super().__init__(entity_name="User", identifier=username)


class GitHubUserSecretByUserIdNotFoundException(EntityNotFoundException):

    def __init__(self, user_id: int):
        super().__init__(entity_name="GitHubUserSecret", identifier=user_id)


class JiraUserByIdNotFoundException(EntityNotFoundException):

    def __init__(self, jira_user_id: int):
        super().__init__(entity_name="JiraUser", identifier=jira_user_id)


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


class SlackClientException(ServiceException):

    def __init__(self, message: str = "Slack API error occurred"):
        super().__init__(message)


class NoSlackChannelsFound(ServiceException):

    def __init__(self):
        super().__init__(f"No channels found invite slack bot first.")
