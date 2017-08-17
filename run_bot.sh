#!/bin/bash

if [ -n "$BOT_SETTINGS_S3" ]; then
   aws s3 cp $BOT_SETTINGS_S3 /opt/elife-bot/settings.py
else # local development
   cp /opt/elife-bot/settings.example.py /etc/elife-bot/settings.py
   ln -sf /etc/elife-bot/settings.py /opt/elife-bot/settings.py
fi

if [ -n "$POA_XML_GENERATION_SETTINGS_S3" ]; then
   aws s3 cp $POA_XML_GENERATION_SETTINGS_S3 /opt/elife-poa-xml-generation/settings.py
else # local development
   cp /opt/elife-poa-xml-generation/settings.example.py /etc/elife-poa-xml-generation/settings.py
   ln -sf /etc/elife-poa-xml-generation/settings.py /opt/elife-poa-xml-generation/settings.py
fi