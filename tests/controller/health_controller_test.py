class HealthControllerTest:

    def test_health(self, client):
        # when
        response = client.get("/health")

        # then
        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}
