FROM python:3.9


WORKDIR /code


COPY ./requirements.txt /code/requirements.txt


RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt


COPY . /code/app

EXPOSE 100

CMD ["fastapi", "run", "app/main.py", "--port", "100"]