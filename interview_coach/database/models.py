

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
