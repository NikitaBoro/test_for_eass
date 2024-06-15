from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import  OAuth2PasswordRequestForm
from typing import List
from datetime import timedelta
import models
import auth

app = FastAPI()

appointments =[]
current_id = 1


#This route will be called when signing in with phone and password and it will return a token that we can use
@app.post("/v1/token", response_model=models.Token)
def login_for_access_token(form_data:OAuth2PasswordRequestForm = Depends()):
    user = auth.authenticate_user(auth.db,form_data.username,form_data.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Incorrect phone or password",headers={"WWW-Authenticate":"Bearer"})
    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(data={"sub":user.phone},expires_delta=access_token_expires)
    return {"access_token": access_token,"token_type":"bearer"}

#Register user
@app.post("/v1/register",response_model=models.User)
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
@app.get("/v1/users/me",response_model=models.User)
def read_users_me(current_user:models.User = Depends(auth.get_current_active_user)):
    return current_user


# Create an appointment
@app.post("/v1/appointments",response_model=models.Appointment)
def create_appointment(appointment:models.Appointment,current_user:models.UserInDB = Depends(auth.get_current_active_user)):
    global current_id
    appointment.id = current_id
    appointment.phone = current_user.phone
    appointment.name = current_user.full_name
    appointments.append(appointment.dict())
    current_id+=1
    return appointment


# Get all appointments for a specific user
@app.get("/v1/appointments",response_model=List[models.Appointment])
def get_appointments(current_user: models.UserInDB = Depends(auth.get_current_active_user)):
    user_appointments = []
    for a in appointments:
        if a["phone"] == current_user.phone:
            user_appointments.append(a)
    if not user_appointments:
        raise HTTPException(status_code=404, detail="Appointments not found")
    return user_appointments

#update appointment by id
@app.put("/v1/appointments/{id}", response_model=models.Appointment)
def update_appointment(id: int, updated_appointment: models.Appointment, current_user: models.UserInDB = Depends(auth.get_current_active_user)):
    for a in appointments:
        if a["id"] == id:
            if a["phone"] == current_user.phone or current_user.role == "admin":
                updated_appointment.id = id
                updated_appointment.phone = a["phone"]
                updated_appointment.name = a["name"]
                appointments[appointments.index(a)] = updated_appointment.dict()
                return updated_appointment
            else:
                raise HTTPException(status_code=403, detail="Not authorized to update this appointment")
    raise HTTPException(status_code=404, detail="Can't update, appointment not found")

#delete appointment by id
@app.delete("/v1/appointments/{id}", response_model=models.Appointment)
def delete_appointment(id: int, current_user: models.UserInDB = Depends(auth.get_current_active_user)):
    for a in appointments:
        if a["id"] == id:
            if a["phone"] == current_user.phone or current_user.role == "admin":
                appointments.remove(a)
                return a
            else:
                raise HTTPException(status_code=403, detail="Not authorized to delete this appointment")
    raise HTTPException(status_code=404, detail="Appointment not found")


# Admin Routes -------------------------------------------------------------------------------------------------------------

#get all users
@app.get("/v1/admin/users")
def read_all_users(current_user:models.User = Depends(auth.get_current_active_admin)):
    return [models.User(**user_data) for user_data in auth.db.values()] 

#admin delete user
@app.delete("/v1/admin/users/{phone}", response_model=models.User)
def delete_user(phone: str, current_user: models.UserInDB = Depends(auth.get_current_active_admin)):
    if phone in auth.db:
        updated_appointments = []
        for appointment in appointments:
            if appointment["phone"] != phone:
                updated_appointments.append(appointment)

        appointments[:] = updated_appointments
        user = auth.db.pop(phone)
        return models.UserInDB(**user)
    raise HTTPException(status_code=404, detail="User not found")

# Admin get all appointments
@app.get("/v1/admin/appointments/all", response_model=List[models.Appointment])
def get_all_appointments(current_user: models.UserInDB = Depends(auth.get_current_active_admin)):
    if not appointments:
        raise HTTPException(status_code=404, detail="Appointments not found")
    return appointments


# Get all appointments for a phone number
@app.get("/v1/admin/appointments/phone/{phone}",response_model=List[models.Appointment])
def get_appointments_by_phone(phone:str, current_user: models.UserInDB = Depends(auth.get_current_active_admin)):
    appointments_list = []
    for a in appointments:
        if a["phone"] == phone:
            appointments_list.append(a)
    if not appointments_list:
        raise HTTPException(status_code=404, detail="Appointments not found for this phone number")
    return appointments_list    

# Get all appointments in a specific month
@app.get("/v1/admin/appointments/month/{month}",response_model=List[models.Appointment])
def get_appointments_by_month(month:int,current_user: models.UserInDB = Depends(auth.get_current_active_admin)):
    appointments_list = []
    for a in appointments:
        appointment_datetime = models.combine_date_time(a["date"], a["time"])
        if appointment_datetime.month == month:
            appointments_list.append(a)
    
    if not appointments_list:
        raise HTTPException(status_code=404, detail="Appointments not found for this month")
    
    return appointments_list 
