import pytest
from app.database import Base, engine, SessionLocal
from app.models import Todo


@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database session for each test."""
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def sample_todo():
    """Create a sample todo data."""
    from app.schemas import TodoCreate
    return TodoCreate(title="Sample Todo", description="Sample Description")
