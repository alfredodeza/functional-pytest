FROM python:3.8

LABEL maintainer="Alfredo Deza"

ARG COMMIT
ARG VERSION

LABEL org.label-schema.vcs-ref=$COMMIT
LABEL org.label-schema.version=$VERSION

COPY ./requirements.txt /webapp/requirements.txt

WORKDIR /webapp

RUN pip install -r requirements.txt

COPY webapp/* /webapp

ENTRYPOINT [ "python" ]

CMD [ "app.py" ]
