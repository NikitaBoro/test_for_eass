from fastapi import APIRouter, Depends, HTTPException
from typing import List
import models
import auth
from data import appointments, current_id

router = APIRouter()

# Create an appointment
@router.post("/appointments",response_model=models.Appointment)
def create_appointment(appointment:models.Appointment,current_user:models.UserInDB = Depends(auth.get_current_active_user)):
    global current_id
    appointment.id = current_id
    appointment.phone = current_user.phone
    appointment.name = current_user.full_name
    appointments.append(appointment.dict())
    current_id+=1
    return appointment


# Get all appointments for a specific user
@router.get("/appointments",response_model=List[models.Appointment])
def get_appointments(current_user: models.UserInDB = Depends(auth.get_current_active_user)):
    user_appointments = []
    for a in appointments:
        if a["phone"] == current_user.phone:
            user_appointments.append(a)
    if not user_appointments:
        raise HTTPException(status_code=404, detail="Appointments not found")
    return user_appointments

#update appointment by id
@router.put("/appointments/{id}", response_model=models.Appointment)
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
@router.delete("/appointments/{id}", response_model=models.Appointment)
def delete_appointment(id: int, current_user: models.UserInDB = Depends(auth.get_current_active_user)):
    for a in appointments:
        if a["id"] == id:
            if a["phone"] == current_user.phone or current_user.role == "admin":
                appointments.remove(a)
                return a
            else:
                raise HTTPException(status_code=403, detail="Not authorized to delete this appointment")
    raise HTTPException(status_code=404, detail="Appointment not found")
