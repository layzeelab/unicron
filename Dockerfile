FROM ubuntu:18.04
LABEL maintainer @layzeelab

RUN apt-get update \
	&& apt-get install -y python3 python3-pip nginx runit \
	&& rm -rf /var/lib/apt/lists/*

RUN pip3 install uwsgi flask celery croniter pytz redis requests jsonschema

ADD ./config/nginx-default /etc/nginx/sites-available/default
RUN echo "\ndaemon off;" >> /etc/nginx/nginx.conf \
	&& ln -sf /dev/stdout /var/log/nginx/access.log \
	&& ln -sf /dev/stderr /var/log/nginx/error.log

COPY ./services/ /etc/service/
RUN chmod +x /etc/service/*/run

COPY ./lib/ /var/unicron/

ENV PYTHONPATH /var/

EXPOSE 80

ENTRYPOINT ["/usr/bin/runsvdir"]
CMD ["/etc/service"]
