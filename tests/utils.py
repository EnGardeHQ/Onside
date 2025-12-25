from datetime import datetime
from unittest.mock import AsyncMock
from sqlalchemy.engine import Result

class MockUser:
    def __init__(self, **kwargs):
        self.id = kwargs.get('id', 1)
        self.email = kwargs.get('email')
        self.metadata = kwargs.get('metadata', {})
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

class MockContent:
    def __init__(self, **kwargs):
        self.id = kwargs.get('id', 1)
        self.title = kwargs.get('title')
        self.text = kwargs.get('text')
        self.content_text = kwargs.get('text')  # Alias for compatibility
        self.user_id = kwargs.get('user_id')
        self.metadata = kwargs.get('metadata', {})
        self.content_metadata = kwargs.get('metadata', {})  # Alias for compatibility
        self.created_at = kwargs.get('created_at', datetime.utcnow())
        self.updated_at = datetime.utcnow()

class MockResult:
    def __init__(self, result):
        self._result = result

    def scalars(self):
        return self

    def all(self):
        if isinstance(self._result, Exception):
            raise self._result
        return self._result

class MockEngagement:
    def __init__(self, **kwargs):
        self.id = kwargs.get('id', 1)
        self.content_id = kwargs.get('content_id')
        self.user_id = kwargs.get('user_id', 1)
        self.date = kwargs.get('date', datetime.utcnow())
        self.views = kwargs.get('views', 0)
        self.likes = kwargs.get('likes', 0)
        self.shares = kwargs.get('shares', 0)
        self.comments = kwargs.get('comments', 0)
        self.metrics = {
            'views': self.views,
            'likes': self.likes,
            'shares': self.shares,
            'comments': self.comments
        }

class MockSession:
    def __init__(self):
        self.execute_result = None
        self.commit = AsyncMock()
        self.rollback = AsyncMock()

    async def execute(self, query):
        if isinstance(self.execute_result, Exception):
            raise self.execute_result
        return self.execute_result
    
    def scalar_one_or_none(self):
        if not hasattr(self, '_scalar_result'):
            return None
        return self._scalar_result

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass

def get_mock_db_session():
    return MockSession()
