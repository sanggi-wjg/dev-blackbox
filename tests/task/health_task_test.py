from dev_blackbox.task.health_task import health_check_task


class HealthTaskTest:

    def test_health_check_task(self):
        # given / when
        result = health_check_task()

        # then
        assert result == {"status": "healthy"}
