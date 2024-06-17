from fastapi import HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer
from typing import Optional
from datetime import datetime , timedelta, timezone
from jose import JWTError ,jwt
from passlib.context import CryptContext
import models
from data import db

SECRET_KEY = "7405114844cf1cc085f408c2d33561cacbcb8530499feabc295df77970d70aeb"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES=30



pwd_context = CryptContext(schemes=["bcrypt"],deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/v1/token")

#function for verifing password
def verify_password(plain_password,hashed_password):
    return pwd_context.verify(plain_password,hashed_password)

#function to hash password
def get_password_hash(password):
    return pwd_context.hash(password)

#get user from DB
def get_user(db,phone:str):
    if phone in db:
        user_data = db[phone]
        return models.UserInDB(**user_data)
    
#function to authenticate if user exists and the password is correct    
def authenticate_user(db,phone: str,password:str):
    user = get_user(db,phone)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user

#function to create access token
def create_access_token(data: dict,expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)

    to_encode.update({"exp":expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(token: str = Depends(oauth2_scheme)):
    credential_exception = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Could not validate credentials",headers={"WWW-Authenticate":"Bearer"})

    try: 
        payload = jwt.decode(token, SECRET_KEY,algorithms=[ALGORITHM])
        phone: str = payload.get("sub")
        if phone is None:
            raise credential_exception
        
        token_data = models.TokenData(phone=phone)
    except JWTError:
        raise credential_exception
    
    user = get_user(db,phone=token_data.phone)
    if user is None:
        raise credential_exception
    
    return user


#check if user disabled and if not return the user
async def get_current_active_user(current_user: models.UserInDB = Depends(get_current_user)):
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


async def get_current_active_admin(current_user: models.UserInDB = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=400, detail="Not enough permissions")
    return current_user
