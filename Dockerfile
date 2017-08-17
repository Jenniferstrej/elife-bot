FROM ubuntu

RUN apt-get update -y && apt-get install -y python-pip libxml2-dev libxslt-dev python-dev python-setuptools build-essential nginx uwsgi libpq-dev uwsgi-plugin-python
RUN apt-get install -y libtiff5-dev libjpeg8-dev zlib1g-dev libfreetype6-dev liblcms2-dev libwebp-dev tcl8.6-dev tk8.6-dev python-tk
RUN apt-get install -y git mercurial

COPY . /opt/elife-bot

RUN pip install -r /opt/elife-bot/requirements.txt

# For development, for mounting volume to add dev settings
RUN mkdir -p /etc/elife-bot
RUN mkdir -p /etc/elife-poa-xml-generation

# Dependency on elife-poa-xml-generation in some activities
RUN git clone https://github.com/elifesciences/elife-poa-xml-generation.git /opt/elife-poa-xml-generation



