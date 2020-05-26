#
# We may want to pin this to a specific version of RabbitMQ.
#
# One issue is that over time older versions of TLS support
# have been deprecated for security reasons. Please see:
# https://www.rabbitmq.com/which-erlang.html
#
FROM rabbitmq:3.6-management

COPY configs /etc/rabbitmq

EXPOSE 5672/tcp
EXPOSE 15672/tcp
