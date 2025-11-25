from pydantic import BaseModel, EmailStr, constr

class UserBase(BaseModel):
    name: str
    email: EmailStr
    password: str

class UserCreate(BaseModel):
    name: str
    email: str
    password: constr(max_length=72, min_length=4)

class UserResponse(UserBase):
    id: int

    class Config:
        orm_mode = True
