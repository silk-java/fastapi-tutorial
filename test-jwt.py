from datetime import timedelta, datetime
from typing import Union

import uvicorn
from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import jwt, JWTError
from passlib.context import CryptContext
from pydantic import BaseModel
from starlette import status

# openssl rand -hex 32
# 使用命令行生成jwt的随机密钥
SECRET_KEY = "25a7a7c926bdc1a840daced5aeaa0f8ed1abebaa975a49522752aa16c4a63fc9"
ALGORITHM = "HS256"  # 算法
ACCESS_TOKEN_EXPIRE_MINUTES = 20  # token过期时间

# 这是数据库中的用户列表
fake_users_db = {
    "johndoe": {
        "username": "johndoe",
        "full_name": "John Doe",
        "email": "johndoe@example.com",
        "hashed_password": "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",
        "disabled": False,
    }
}


class Token(BaseModel):
    """
    token返回对象
    """
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Union[str, None] = None


class User(BaseModel):
    username: str
    email: Union[str, None] = None
    full_name: Union[str, None] = None
    disabled: Union[bool, None] = None


# 继承了User类，存储与数据库的user
class UserInDB(User):
    hashed_password: str


# 这是一个实例对象
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# 这是一个实例对象
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")

app = FastAPI()


def verify_password(plain_password, hashed_password) -> bool:
    """
    校验密码是否正确
    :param plain_password: 密码明文
    :param hashed_password: 加密后的密码
    :return: 校验结果
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password) -> str:
    """
    获取密码的hash值
    :param password: 密码明文
    :return: 密码hash值
    """
    return pwd_context.hash(password)


def get_user(db: dict, username: str):
    """
    从数据库中获取用户
    :param db: 数据库,此处假设为字典
    :param username:  用户名
    :return: 用户信息
    """
    if username in db:
        user_dict = db[username]
        return UserInDB(**user_dict)


def authenticate_user(fake_db: dict, username: str, password: str):
    """
    验证用户身份
    :param fake_db:
    :param username:
    :param password:
    :return:
    """
    # 从数据库获取数据库中的用户对象
    user = get_user(fake_db, username)
    if not user:
        # 如果数据库中没有这个用户，返回false
        return False
    if not verify_password(password, user.hashed_password):
        # 如果数据库中有这个用户，但是密码校验不通过，返回false
        return False
    return user


def create_access_token(data: dict, expires_delta: Union[timedelta, None] = None):
    """
    生成token
    :param data: 用户信息
    :param expires_delta: 过期时间
    :return: 利用用户信息生成的token
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(token: str = Depends(oauth2_scheme)):
    """
    获取当前用户
    :param token:
    :return:
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        # 利用jwt解析请求头中的token值，获取实际的用户信息
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get('sub')
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    user = get_user(fake_users_db, username=token_data.username)
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(current_user: User = Depends(get_current_user)):
    """
    获取当前用户
    :param current_user: 当前用户
    :return:
    """
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


@app.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(fake_users_db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username},
        expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/users/me/", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    """
    获取当前用户
    :param current_user:
    :return:
    """
    return current_user


@app.get("/users/me/items/")
async def read_own_items(current_user: User = Depends(get_current_active_user)):
    """
    获取当前用户拥有的物品
    :param current_user:
    :return:
    """
    return [{"item_id": "Foo", "owner": current_user.username}]


if __name__ == '__main__':
    uvicorn.run('test-jwt:app', host='0.0.0.0', port=8000, reload=True, debug=True, workers=1)
