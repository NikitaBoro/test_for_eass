from fastapi import APIRouter, Depends, HTTPException,status
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta
import models
import auth
from data import db

router = APIRouter()


#This route will be called when signing in with phone and password and it will return a token that we can use
@router.post("/token", response_model=models.Token)
def login_for_access_token(form_data:OAuth2PasswordRequestForm = Depends()):
    user = auth.authenticate_user(auth.db,form_data.username,form_data.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Incorrect phone or password",headers={"WWW-Authenticate":"Bearer"})
    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(data={"sub":user.phone},expires_delta=access_token_expires)
    return {"access_token": access_token,"token_type":"bearer"}

#Register user
@router.post("/register",response_model=models.User)
def register_user(user:models.User,password:str):
    if user.phone in auth.db:
        raise HTTPException(status_code=400, detail="Phone already registerd")
    hashed_password = auth.pwd_context.hash(password)
    user_data = user.dict()
    user_data["hashed_password"] = hashed_password
    user_data["role"] = "user"
    auth.db[user.phone] = user_data
    return models.UserInDB(**user_data)

#Get logged user information
@router.get("/users/me",response_model=models.User)
def read_users_me(current_user:models.User = Depends(auth.get_current_active_user)):
    return current_user
