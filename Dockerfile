FROM python:bullseye

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install -U py-cord --pre
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD [ "python", "-m", "aprsdiscord" ]