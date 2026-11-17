FROM python:3.12-slim

LABEL "com.github.actions.name"="Notify Dependency Updates Teams Action"
LABEL "com.github.actions.description"="Sends a dependency updates notification to Microsoft Teams"
LABEL "com.github.actions.icon"="package"
LABEL "com.github.actions.color"="blue"

COPY notify_dependency_updates_teams.py /app/notify_dependency_updates_teams.py
RUN pip install --no-cache-dir "requests>=2.32,<3"

ENTRYPOINT ["python", "/app/notify_dependency_updates_teams.py"]
