FROM python:3-alpine

RUN apk add git

WORKDIR /app
COPY requirements.txt ./
RUN pip3 install --no-cache-dir -r requirements.txt
COPY stage-messages-amqp ./

ENTRYPOINT ["python3", "-u", "/app/stage-messages-amqp"]
CMD ["amqp://worker:worker@rabbitmq", "messages", "0", "amqp://worker:worker@rabbitmq", "to-beehive"]
