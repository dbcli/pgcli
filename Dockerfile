FROM python:2.7

COPY . /app
RUN cd /app && pip install -e .

CMD pgcli
