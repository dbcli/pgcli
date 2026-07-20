FROM python:3.14

COPY . /app
RUN cd /app && pip install -e .

CMD pgcli
