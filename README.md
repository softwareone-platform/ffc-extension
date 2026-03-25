[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff) [![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=softwareone-platform_ffc-finops-operations&metric=alert_status)](https://sonarcloud.io/summary/new_code?id=softwareone-platform_ffc-finops-operations) [![Coverage](https://sonarcloud.io/api/project_badges/measure?project=softwareone-platform_ffc-finops-operations&metric=coverage)](https://sonarcloud.io/summary/new_code?id=softwareone-platform_ffc-finops-operations)

# SoftwareOne FinOps for Cloud Operations API

The Operations API enables SoftwareOne to manage the FinOps for Cloud tool. It supports the provisioning and administration of FinOps for Cloud organizations and users, as well as the management of datasource entitlements.

# Create you .env file

You can use the `env.example` as a bases to setup your running environment and customize it according to your needs.

# Run tests

`docker compose run --rm app_test`

# Run for Development

`docker compose up app`

# Build production image

To build the production image please use the `prod.Dockefile` dockerfile.

> [!IMPORTANT]
> Developers must take care of keep in sync `dev.Dockerfile` and `prod.Dockerfile`.
