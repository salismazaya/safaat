FROM python:3.10.12-alpine

WORKDIR /app

COPY . .

RUN pip install -r requirements.txt

RUN python manage.py collectstatic --no-input

CMD gunicorn project.wsgi