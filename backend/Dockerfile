FROM python:3.8-slim-buster

RUN pip install flask

COPY backend.py /

ENV FLASK_APP=backend.py

# EXPOSE 7000
CMD ["flask", "run", "--host=0.0.0.0", "--port=7000"]
