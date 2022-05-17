FROM python:bullseye

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install -U git+https://github.com/Pycord-Development/pycord
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD [ "python", "-m", "aprsdiscord" ]