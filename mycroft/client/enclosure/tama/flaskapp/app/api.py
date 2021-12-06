import datetime
from tornado.gen import coroutine
from tornado_sqlalchemy import as_future
from todo.models import Profile, Task

# the BaseView is above here
class TaskListView(BaseView):
    """View for reading and adding new tasks."""
    SUPPORTED_METHODS = ("GET", "POST",)

    @coroutine
    def get(self, username):
        """Get all tasks for an existing user."""
        with self.make_session() as session:
            profile = yield as_future(session.query(Profile).filter(Profile.username == username).first)
            if profile:
                tasks = [task.to_dict() for task in profile.tasks]
                self.send_response({
                    'username': profile.username,
                    'tasks': tasks
                })