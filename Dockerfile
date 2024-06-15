FROM python:3.10.14

WORKDIR /app

COPY ./backend/requirements.txt .

RUN pip install -r requirements.txt

COPY ./backend/main.py .
COPY ./backend/models.py .
COPY ./backend/auth.py .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]