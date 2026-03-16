from dev_blackbox.core.enum import TaskStatusEnum
from dev_blackbox.storage.rds.repository.task_repository import TaskRepository


class TaskRepositoryTest:

    def test_keyword로_title_검색(self, db_session, user_fixture, task_fixture):
        repository = TaskRepository(db_session)

        # given
        user = user_fixture("task_kw_title@dev.com")
        task_fixture(user_id=user.id, title="Deploy 서버 배포")
        task_fixture(user_id=user.id, title="버그 수정")

        # when
        result = repository.find_all_by_user_id_and_filters(user.id, query="deploy")

        # then
        assert len(result) == 1
        assert result[0].title == "Deploy 서버 배포"

    def test_keyword로_content_검색(self, db_session, user_fixture, task_fixture):
        repository = TaskRepository(db_session)

        # given
        user = user_fixture("task_kw_content@dev.com")
        task_fixture(user_id=user.id, title="태스크1", content="서버 deploy 관련 작업")
        task_fixture(user_id=user.id, title="태스크2", content="문서 작성")

        # when
        result = repository.find_all_by_user_id_and_filters(user.id, query="deploy")

        # then
        assert len(result) == 1
        assert result[0].title == "태스크1"

    def test_keyword로_tags_검색(self, db_session, user_fixture, task_fixture):
        repository = TaskRepository(db_session)

        # given
        user = user_fixture("task_kw_tags@dev.com")
        task_fixture(user_id=user.id, title="태스크1", tags="backend,deploy")
        task_fixture(user_id=user.id, title="태스크2", tags="frontend")

        # when
        result = repository.find_all_by_user_id_and_filters(user.id, query="deploy")

        # then
        assert len(result) == 1
        assert result[0].title == "태스크1"

    def test_keyword_대소문자_무시(self, db_session, user_fixture, task_fixture):
        repository = TaskRepository(db_session)

        # given
        user = user_fixture("task_kw_case@dev.com")
        task_fixture(user_id=user.id, title="DEPLOY 작업")

        # when
        result = repository.find_all_by_user_id_and_filters(user.id, query="deploy")

        # then
        assert len(result) == 1

    def test_keyword와_status_필터_조합(self, db_session, user_fixture, task_fixture):
        repository = TaskRepository(db_session)

        # given
        user = user_fixture("task_kw_status@dev.com")
        task_fixture(user_id=user.id, title="Deploy 태스크", status=TaskStatusEnum.IN_PROGRESS)
        task_fixture(user_id=user.id, title="Deploy 완료", status=TaskStatusEnum.DONE)

        # when
        result = repository.find_all_by_user_id_and_filters(
            user.id, statuses=[TaskStatusEnum.IN_PROGRESS], query="deploy"
        )

        # then
        assert len(result) == 1
        assert result[0].title == "Deploy 태스크"

    def test_keyword_없으면_전체_조회(self, db_session, user_fixture, task_fixture):
        repository = TaskRepository(db_session)

        # given
        user = user_fixture("task_kw_none@dev.com")
        task_fixture(user_id=user.id, title="태스크1")
        task_fixture(user_id=user.id, title="태스크2")

        # when
        result = repository.find_all_by_user_id_and_filters(user.id)

        # then
        assert len(result) == 2

    def test_keyword_매칭_없으면_빈_결과(self, db_session, user_fixture, task_fixture):
        repository = TaskRepository(db_session)

        # given
        user = user_fixture("task_kw_empty@dev.com")
        task_fixture(user_id=user.id, title="태스크1")

        # when
        result = repository.find_all_by_user_id_and_filters(user.id, query="없는키워드xyz")

        # then
        assert len(result) == 0
