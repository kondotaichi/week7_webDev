from sqlalchemy import create_engine
from models import Base

engine = create_engine('sqlite:///chatapp.db', echo=True)
Base.metadata.create_all(bind=engine)

print("✅ データベースとテーブル作成完了！")
