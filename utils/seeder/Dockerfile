FROM python:3.11-bullseye

ARG VERSION
ENV VERSION $VERSION

ARG api_key
ENV api_key $api_key

COPY . /opt/seeder
WORKDIR /opt/seeder

RUN pip install --upgrade pip
RUN pip install -r requirements.txt

CMD ["python3", "-u", "seeder.py"]
