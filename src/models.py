from pydantic import BaseModel
from typing import List, Optional
from sqlmodel import SQLModel, Field, Session, create_engine, select


class UserCreate(BaseModel):
    username: str
    password: str

class UserProfile(BaseModel):
    id: int
    username: str
    profile_picture: Optional[str]

class FlowerCreate(BaseModel):
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

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True)
    password: str
    profile_picture: Optional[str] = None

class Flower(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    price: float

class Purchase(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int
    flower_id: int
