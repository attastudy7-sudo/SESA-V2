from locust import HttpUser, task

class MyUser(HttpUser):
    @task
    def index(self):
        self.client.get("/")
