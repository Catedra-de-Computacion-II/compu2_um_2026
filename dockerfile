FROM python:3.10

WORKDIR /app

COPY race_cond.py .

CMD ["python", "race_cond.py"]
