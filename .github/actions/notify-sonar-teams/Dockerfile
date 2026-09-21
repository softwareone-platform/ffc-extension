FROM python:3.12-slim

LABEL "com.github.actions.name"="Notify Sonar Quality Gate Teams Action"
LABEL "com.github.actions.description"="Sends a Sonar quality gate notification to Microsoft Teams"
LABEL "com.github.actions.icon"="check-circle"
LABEL "com.github.actions.color"="blue"

COPY notify_sonar_teams.py /app/notify_sonar_teams.py
RUN pip install --no-cache-dir "requests>=2.32,<3"

ENTRYPOINT ["python", "/app/notify_sonar_teams.py"]
