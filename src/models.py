from pydantic import BaseModel
from typing import List, Optional
from sqlmodel import SQLModel, Field, Session, create_engine, select


class UserCreate(SQLModel):
    username: str
    password: str

class UserProfile(BaseModel):
    id: int
    username: str
    profile_picture: Optional[str]

class FlowerCreate(SQLModel):
    name: str
    price: float

class FlowerResponse(BaseModel):
    id: int
    name: str
    price: float

class CartItem(BaseModel):
    id: int
    name: str
    price: float

class PurchaseResponse(BaseModel):
    name: str
    price: float

class User(UserCreate, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    profile_picture: Optional[str] = None

class Flower(FlowerCreate, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

class Purchase(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int
    flower_id: int
