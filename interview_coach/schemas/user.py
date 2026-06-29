from pydantic import BaseModel, EmailStr

class UserCreate(BaseModel):
    fullname: str
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: int
    fullname: str
    email: str

    class Config:
        from_attributes = True