FROM selenium/standalone-edge:121.0
# lxml not working in python 3.12

USER root

RUN apt-get update && \
    apt-get install -y libxml2-dev libxslt-dev build-essential libssl-dev libffi-dev python3-dev python3-pip && \
    apt-get clean

ENV DISPLAY=:99

WORKDIR /app

COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

RUN playwright install 

COPY . .
EXPOSE 80
CMD ["python3", "-u", "src/main2.py"]