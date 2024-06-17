from fastapi import APIRouter, Depends, HTTPException
from typing import List
import models
import auth
from data import appointments, db

router = APIRouter()

# Get all users
@router.get("/users")
def read_all_users(current_user:models.User = Depends(auth.get_current_active_admin)):
    return [models.User(**user_data) for user_data in db.values()] 

#A dmin delete user
@router.delete("/users/{phone}", response_model=models.User)
def delete_user(phone: str, current_user: models.UserInDB = Depends(auth.get_current_active_admin)):
    if phone in db:
        updated_appointments = []
        for appointment in appointments:
            if appointment["phone"] != phone:
                updated_appointments.append(appointment)

        appointments[:] = updated_appointments
        user = db.pop(phone)
        return models.UserInDB(**user)
    raise HTTPException(status_code=404, detail="User not found")

# Admin get all appointments
@router.get("/appointments/all", response_model=List[models.Appointment])
def get_all_appointments(current_user: models.UserInDB = Depends(auth.get_current_active_admin)):
    if not appointments:
        raise HTTPException(status_code=404, detail="Appointments not found")
    return appointments


# Get all appointments for a phone number
@router.get("/appointments/phone/{phone}",response_model=List[models.Appointment])
def get_appointments_by_phone(phone:str, current_user: models.UserInDB = Depends(auth.get_current_active_admin)):
    appointments_list = []
    for a in appointments:
        if a["phone"] == phone:
            appointments_list.append(a)
    if not appointments_list:
        raise HTTPException(status_code=404, detail="Appointments not found for this phone number")
    return appointments_list    

# Get all appointments in a specific month
@router.get("/appointments/month/{month}",response_model=List[models.Appointment])
def get_appointments_by_month(month:int,current_user: models.UserInDB = Depends(auth.get_current_active_admin)):
    appointments_list = []
    for a in appointments:
        appointment_datetime = models.combine_date_time(a["date"], a["time"])
        if appointment_datetime.month == month:
            appointments_list.append(a)
    
    if not appointments_list:
        raise HTTPException(status_code=404, detail="Appointments not found for this month")
    
    return appointments_list 
