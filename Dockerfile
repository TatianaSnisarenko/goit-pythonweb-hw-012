FROM python:3.12-alpine3.20
ENV APP_HOME /app
WORKDIR $APP_HOME
COPY . .
RUN pip install -r requirements.txt
RUN chmod +x start.sh
EXPOSE 8080
ENTRYPOINT ["./start.sh"]