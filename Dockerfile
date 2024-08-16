FROM python:3.10.4
RUN apt-get -y update
RUN mkdir -p /app/nyah-bot
WORKDIR /app/nyah-bot
COPY ./ /app/nyah-bot
RUN pip install --no-cache-dir -r requirements.txt
ENTRYPOINT python /app/nyah-bot/launcher.py