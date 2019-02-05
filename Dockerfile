FROM python:3-alpine

COPY requirements.txt /
RUN pip install -r /requirements.txt
COPY pokemon.csv pokemon.py /

CMD ["python3", "/pokemon.py"]
