from pydantic import BaseModel , field_validator
from datetime import datetime
from typing import List, Optional


class Token(BaseModel):
    access_token : str
    token_type: str

class TokenData(BaseModel):
    phone: Optional[str] = None

class User(BaseModel):
    phone: str
    full_name: str
    email: Optional[str] = None
    disabled: Optional[bool] = False
    role: str

class UserInDB(User):
    hashed_password: str




class Appointment(BaseModel):
    id:int
    name: str
    phone: str
    date: str # dd-mm-yyyy format
    time: str # hh:mm format
    service: str


    @field_validator("date")
    def check_date(cls, value):
        formmated_date = datetime.strptime(value, "%d-%m-%Y").date()
        if formmated_date < datetime.now().date():
            raise ValueError("Invalid date")
        return value

    @field_validator('time')
    def check_time(cls, value):
        try:
            datetime.strptime(value, "%H:%M")
        except ValueError:
            raise ValueError('Invalid time: Time must be in the format HH:MM.')
        return value


def combine_date_time(date:str,time:str) -> datetime:
    date_time = f"{date} {time}"
    return datetime.strptime(date_time, "%d-%m-%Y %H:%M")


