FROM python:3.10.8-slim-buster

ARG API_ID

RUN apt update && apt upgrade -y

RUN apt install git -y

COPY requirements.txt /requirements.txt

RUN pip3 install -U pip && pip3 install -U -r requirements.txt

RUN mkdir /DQTheFileDonor

WORKDIR /DQTheFileDonor

COPY start.sh /start.sh

EXPOSE 8080

ENV API_ID=$API_ID

RUN echo "API_ID=$API_ID" >> /etc/environment

CMD ["/bin/bash", "/start.sh"]