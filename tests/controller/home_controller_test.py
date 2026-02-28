class HomeControllerTest:

    def test_index(self, client):
        # when
        response = client.get("/")

        # then
        assert response.status_code == 200
        assert response.json() == {"message": "Hello World"}
