from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from app.infra.settings import SETTINGS

mysql_url = SETTINGS.MYSQL_URL
engine = create_engine(mysql_url, pool_recycle=300)

DbSession = sessionmaker(bind=engine, autoflush=True, expire_on_commit=True)
Base = declarative_base()
Base.metadata.create_all(bind=engine)