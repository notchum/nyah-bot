FROM python:3.10.4
RUN apt-get -y update
RUN mkdir -p /opt/nyah-bot
WORKDIR /opt/nyah-bot
COPY ./ /opt/nyah-bot
RUN pip install --no-cache-dir -r requirements.txt
ENTRYPOINT python /opt/nyah-bot/bot.py