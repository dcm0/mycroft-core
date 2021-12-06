# all the previous imports
import datetime
from tornado.gen import coroutine
from tornado_sqlalchemy import as_future


# the BaseView is above here
class TaskListView(BaseView):
    """View for reading and adding new tasks."""
    SUPPORTED_METHODS = ("GET", "POST",)

    @coroutine
    def get(self, username):
        """Get all tasks for an existing user."""
        with self.make_session() as session:
            self.send_response({
                'username': 'Tama page',
                'tasks': 'Tama Woz'
            })