FROM python:3.9

COPY . /app
RUN cd /app && pip install -e .

CMD pgcli
