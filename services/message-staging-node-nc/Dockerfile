FROM waggle/plugin-base:0.1.0

WORKDIR /app
COPY requirements.txt ./
RUN pip3 install --no-cache-dir -r requirements.txt

# hot fix for pywaggle to use rabbitmq hostname, instead of localhost
RUN pywaggle_loc=$(pip3 show waggle | grep Location | cut -d ':' -f 2 | tr -d ' ') \
  && sed -i 's|amqp://localhost|amqp://rabbitmq|g' ${pywaggle_loc}/waggle/pipeline.py

COPY stage-messages-amqp ./

ENTRYPOINT ["python3", "-u", "/app/stage-messages-amqp"]
CMD ["amqp://worker:worker@rabbitmq", "messages", "0", "amqp://worker:worker@rabbitmq", "to-beehive"]
