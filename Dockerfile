FROM python:3.9-slim

RUN apt update -y && \
    apt install -y gcc

WORKDIR /app

# Install dependencies
COPY requirements.txt requirements.dev /app
RUN pip install -r requirements.dev

COPY . /app
