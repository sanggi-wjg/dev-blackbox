class UserControllerTest:

    def test_users_me(self, client, authenticated_user):
        # when
        response = client.get("/api/v1/users/me")

        # then
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == authenticated_user.id
        assert data["email"] == "test@dev.com"
