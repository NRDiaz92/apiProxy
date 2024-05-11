FROM python:3.10 AS base_image

ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && \
    apt-get install python3-dev python3-urllib3 -y && \
    apt-get upgrade -y

FROM base_image AS code_image

ADD src .

RUN pip install --upgrade pip && pip install --upgrade -r requirements.txt

ENTRYPOINT ["gunicorn"]
CMD ["-b", "0.0.0.0:80", "app:app", "-w", "4", "--threads", "10"]