FROM python:3.9-slim-buster

WORKDIR /fb-receives

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt
RUN apt-get update && apt-get install -y nano

COPY . .

CMD ["python", "bling_sources.py"]
