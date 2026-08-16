class UserGateway:
    def load(self, user_id):
        return self.client.users.fetch(user_id)
