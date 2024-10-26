FROM python:3.11
LABEL authors="cliftbar"

WORKDIR backtrack

COPY ./requirements ./requirements


RUN sh ./requirements/install.sh

COPY ./src ./src
WORKDIR src

ENV PYTHONUNBUFFERED=1

CMD ["fastapi", "run", "backtrack/main.py"]
