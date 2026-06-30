from pydantic import BaseModel, EmailStr

class UserCreate(BaseModel):
    fullname: str
    email: EmailStr
    password: str
    target_role: str


class UserResponse(BaseModel):
    id: int
    fullname: str
    email: str
    target_role: str

    class Config:
        from_attributes = True