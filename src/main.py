from fastapi import FastAPI, Depends, HTTPException, Form, UploadFile, File, Cookie
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.responses import JSONResponse
from sqlmodel import SQLModel, Field, Session, create_engine, select
from typing import List, Optional
from pydantic import BaseModel
from passlib.context import CryptContext
from jose import JWTError, jwt
import os
from datetime import datetime, timedelta
from config.db_connect import engine
from models import User, UserCreate, UserProfile, Flower, FlowerCreate, FlowerResponse, Purchase, PurchaseResponse

SECRET_KEY = "secret"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

app = FastAPI()


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


@app.post("/signup", response_model=UserProfile)
async def signup(user: UserCreate, profile_picture: UploadFile = File(...)):
    with Session(engine) as session:
        existing_user = session.exec(select(User).where(User.username == user.username)).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="Username already registered")

        db_user = User(
            username=user.username,
            password=get_password_hash(user.password),
            profile_picture=profile_picture.filename,
        )
        session.add(db_user)
        session.commit()
        session.refresh(db_user)

        uploads_dir = "uploads"
        os.makedirs(uploads_dir, exist_ok=True)
        file_path = os.path.join(uploads_dir, profile_picture.filename)
        with open(file_path, "wb") as f:
            f.write(profile_picture.file.read())

        return db_user


@app.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    with Session(engine) as session:
        user = session.exec(select(User).where(User.username == form_data.username)).first()
        if not user or not verify_password(form_data.password, user.password):
            raise HTTPException(status_code=400, detail="Incorrect username or password")
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(data={"sub": user.username}, expires_delta=access_token_expires)
        return {"access_token": access_token, "token_type": "bearer"}


@app.get("/profile", response_model=UserProfile)
def read_profile(token: str = Depends(OAuth2PasswordBearer(tokenUrl="login"))):
    with Session(engine) as session:
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            username: str = payload.get("sub")
            if username is None:
                raise HTTPException(status_code=401, detail="Invalid authentication credentials")
        except JWTError:
            raise HTTPException(status_code=401, detail="Invalid authentication credentials")

        user = session.exec(select(User).where(User.username == username)).first()
        return user


@app.get("/flowers", response_model=List[FlowerResponse])
def get_flowers():
    with Session(engine) as session:
        flowers = session.exec(select(Flower)).all()
        return flowers


@app.post("/flowers", response_model=FlowerResponse)
def create_flower(flower: FlowerCreate):
    with Session(engine) as session:
        db_flower = Flower(name=flower.name, price=flower.price)
        session.add(db_flower)
        session.commit()
        session.refresh(db_flower)
        return db_flower


@app.post("/cart/items")
def add_to_cart(flower_id: int = Form(...), cart: str = Cookie(default="")):
    if cart:
        cart_list = cart.split(",")
    else:
        cart_list = []

    if str(flower_id) not in cart_list:
        cart_list.append(str(flower_id))

    response = JSONResponse(status_code=200)
    response.set_cookie(key="cart", value=",".join(cart_list))
    return response


@app.get("/cart/items")
def get_cart_items(cart: str = Cookie(default="")):
    with Session(engine) as session:
        if not cart:
            return []

        flower_ids = cart.split(",")
        flowers = session.exec(select(Flower).where(Flower.id.in_(flower_ids))).all()

        total_price = sum(flower.price for flower in flowers)
        return {"items": flowers, "total_price": total_price}


@app.post("/purchased")
def purchase(cart: str = Cookie(default=""), token: str = Depends(OAuth2PasswordBearer(tokenUrl="login"))):
    with Session(engine) as session:
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            username: str = payload.get("sub")
        except JWTError:
            raise HTTPException(status_code=401, detail="Invalid authentication credentials")

        user = session.exec(select(User).where(User.username == username)).first()

        if cart:
            flower_ids = cart.split(",")
            for flower_id in flower_ids:
                purchase = Purchase(user_id=user.id, flower_id=int(flower_id))
                session.add(purchase)
            session.commit()

        response = JSONResponse(status_code=200)
        response.delete_cookie(key="cart")
        return response


@app.get("/purchased", response_model=List[PurchaseResponse])
def get_purchased(token: str = Depends(OAuth2PasswordBearer(tokenUrl="login"))):
    with Session(engine) as session:
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            username: str = payload.get("sub")
        except JWTError:
            raise HTTPException(status_code=401, detail="Invalid authentication credentials")

        user = session.exec(select(User).where(User.username == username)).first()
        purchases = session.exec(select(Purchase).where(Purchase.user_id == user.id)).all()

        flower_ids = [purchase.flower_id for purchase in purchases]
        flowers = session.exec(select(Flower).where(Flower.id.in_(flower_ids))).all()

        return [{"name": flower.name, "price": flower.price} for flower in flowers]
