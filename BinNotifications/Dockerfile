FROM python:3.12

ARG TARGET_DIR="/usr/src/app"
ARG CRON_LOG="/var/log/BinCollections.log"
WORKDIR ${TARGET_DIR}


# Install Chromium and ChromeDriver
RUN apt-get update && apt-get install -y \
    chromium \
    chromium-driver \
    cron \
    && rm -rf /var/lib/apt/lists/*

#COPY GetBinCollections.py requirements.txt token.pickle credentials.json ./
COPY GetBinCollections.py requirements.txt bincollections.env .env ./

RUN pip install --no-cache-dir -r requirements.txt

# Set environment variable so Selenium knows where Chrome is if needed
ENV CHROME_BIN=/usr/bin/chromium
ENV CHROMEDRIVER_PATH=/usr/bin/chromedriver

RUN touch ${CRON_LOG}

# Setup cron jobcrontab -l
RUN (crontab -l ; echo "0 4 * * 2 . /etc/environment; /usr/local/bin/python ${TARGET_DIR}/GetBinCollections.py >> ${CRON_LOG} 2>&1") | crontab


# Run the command on container startup
ENTRYPOINT ["/bin/sh", "-c", "printenv >> /etc/environment && cron && tail -f ${CRON_LOG}"]