FROM python:3.10.14

WORKDIR /app

COPY ./backend/requirements.txt .

RUN pip install -r requirements.txt

COPY ./backend/main.py .
COPY ./backend/models.py .
COPY ./backend/auth.py .
COPY ./backend/routes/user_route.py .
COPY ./backend/routes/appointments_route.py .
COPY ./backend/routes/admin_route.py .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]