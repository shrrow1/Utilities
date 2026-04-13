FROM python:3.12

WORKDIR /usr/src/app

# Install Chromium and ChromeDriver
RUN apt-get update && apt-get install -y \
    chromium \
    chromium-driver \
    && rm -rf /var/lib/apt/lists/*

COPY GetBinCollections.py requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Set environment variable so Selenium knows where Chrome is if needed
ENV CHROME_BIN=/usr/bin/chromium
ENV CHROMEDRIVER_PATH=/usr/bin/chromedriver

CMD [ "python", "./GetBinCollections.py" ]

### Why this works:
#1.  **Architecture Match**: By using `apt-get install chromium`, Debian (the base of the Python image) fetches the binary built specifically for your architecture (`aarch64` for ARM/Mac or `x86_64` for Intel).
#2.  **Binary Location**: The updated Python code explicitly checks for `/usr/bin/chromium`, ensuring it doesn't try to download a generic version that might not run on your CPU.
#3.  **No Sandbox**: Running as root in Docker requires the `--no-sandbox` flag, which I've added to the script.