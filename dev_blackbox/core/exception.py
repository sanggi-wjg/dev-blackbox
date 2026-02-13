class ServiceException(Exception):

    def __init__(self, message: str = "Service error occurred"):
        self.message = message
        super().__init__(self.message)


class EntityNotFoundException(ServiceException):

    def __init__(self, entity_name: str, identifier: int | str):
        self.entity_name = entity_name
        self.identifier = identifier
        super().__init__(f"{entity_name} not found by {identifier}")


class UserByIdNotFoundException(EntityNotFoundException):

    def __init__(self, user_id: int):
        super().__init__(entity_name="User", identifier=user_id)


class UserByNameNotFoundException(EntityNotFoundException):

    def __init__(self, username: str):
        super().__init__(entity_name="User", identifier=username)
