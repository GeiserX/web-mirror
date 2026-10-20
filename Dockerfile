FROM selenium/standalone-edge:155.0
# lxml not working in python 3.12

USER root

# ca-certificates is listed to upgrade it: the base image's bundle still trusts
# the compromised eMudhra intermediates.
RUN apt-get update && \
    apt-get install -y ca-certificates libxml2-dev libxslt-dev build-essential libssl-dev libffi-dev python3-dev python3-pip && \
    apt-get clean

ENV DISPLAY=:99

WORKDIR /app

COPY requirements.txt .
RUN pip3 install --no-cache-dir --break-system-packages -r requirements.txt

RUN playwright install 

# Edge and Chromium trust their own root store, not the system one. This managed
# policy distrusts the eight eMudhra intermediates revoked for a key compromise
# on 2026-10-18. Chrome for Testing is the Chromium that Playwright downloads.
COPY policies/distrusted-cas.json /etc/opt/edge/policies/managed/distrusted-cas.json
COPY policies/distrusted-cas.json /etc/opt/chrome_for_testing/policies/managed/distrusted-cas.json

COPY . .
EXPOSE 80
CMD ["python3", "-u", "src/main2.py"]
