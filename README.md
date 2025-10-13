<div align="center">

# Python Package Template

The template repository for creating python packages, shared across auth-broker.

![Python](https://img.shields.io/badge/Python-3.12-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)
![UV](https://img.shields.io/badge/UV-Fast-6E40C9?style=for-the-badge)
![Hatchling](https://img.shields.io/badge/Hatchling-PEP517-6E40C9?style=for-the-badge)
![Ruff](https://img.shields.io/badge/Ruff-Lint-000000?style=for-the-badge)
![Pre-commit](https://img.shields.io/badge/Pre--commit-Hooks-000000?style=for-the-badge)
![Pytest](https://img.shields.io/badge/Pytest-Unit%2BAsync-08979C?style=for-the-badge)
![Coverage](https://img.shields.io/badge/Cov-Reports-08979C?style=for-the-badge)
![GitHub Actions](https://img.shields.io/badge/Actions-CI%2FCD-F7B500?style=for-the-badge&logo=github-actions)
![PyPI](https://img.shields.io/badge/PyPI-Publish-6E40C9?style=for-the-badge)
![Makefile](https://img.shields.io/badge/Makefile-Scripts-F7B500?style=for-the-badge)

🦜🕸️

[![CI](https://github.com/auth-broker/package-template/actions/workflows/ci.yaml/badge.svg?branch=main)](https://github.com/auth-broker/package-template/actions/workflows/ci.yaml)

</div>

______________________________________________________________________

## Template Checklist

- \[ \] Rename module `src/ab_core/template` ->
  `src/ab_core/your_package_name`
- \[ \] Rename tests module `src/ab_core/template` ->
  `src/ab_core/your_package_name`
- \[ \] Update `pyproject.toml`: `[project]` section based on your package name
  / versioning etc.
- \[ \] Update `README.md` references of `python-package-template` ->
  `your-package-name`
- \[ \] Remove this section

______________________________________________________________________

## Table of Contents

<!-- toc -->

- [Introduction](#introduction)
- [Quick Start](#quick-start)
- [Installation](#installation)
- [Usage](#usage)
- [Formatting and linting](#formatting-and-linting)
- [CICD](#cicd)

<!-- tocstop -->

______________________________________________________________________

## Introduction

This template repository aims to create a reusable package template which
streamlines the creation and publishing of isolated python packages in auth-broker.
This is aligned with the engineering vision @ auth-broker for better modularisation and
reusability of code.

______________________________________________________________________

## Quick Start

Since this is just a package, and not a service, there is no real "run" action.
But you can run the tests immediately.

Here are a list of available commands via make.

### Bare Metal (i.e. your machine)

1. `make install` - install the required dependencies.
1. `make test` - runs the tests.

### Docker

1. `make build-docker` - build the docker image.
1. `make run-docker` - run the docker compose services.
1. `make test-docker` - run the tests in docker.
1. `make clean-docker` - remove all docker containers etc.

______________________________________________________________________

## Installation

### For Dev work on the repo

Install `uv`, (_if you haven't already_)
https://docs.astral.sh/uv/getting-started/installation/#installation-methods

```shell
brew install uv
```

Initialise pre-commit (validates ruff on commit.)

```shell
uv run pre-commit install
```

Install dependencies (including dev dependencies)

```shell
uv sync
```

If you are adding a new dev dependency, please run:

```shell
uv add --dev {your-new-package}
```

### Namespaces

Packages all share the same namespace `ab_core`. To import this package into
your project:

```python
from ab_core.template import placeholder_func
```

We encourage you to make your package available to all of ab via this
`ab_core` namespace. The goal is to streamline development, POCs and overall
collaboration.

______________________________________________________________________

## Usage

### Adding the dependency to your project

The library is available on PyPI. You can install it using the following
command:

**Using pip**:

```shell
pip install python-package-template
```

**Using UV**

Note: there is currently no nice way like poetry, hence we still needd to
provide the full url. https://github.com/astral-sh/uv/issues/10140

Add the dependency

```shell
uv add python-package-template
```

**Using poetry**:

Then run the following command to install the package:

```shell
poetry add python-package-template
```

### How tos

**Example Usage**

```python
# Please update this based on your package!

from ab_core.template import placeholder_func


if __name__ == "__main__":
    print("This is a placeholder: ", placeholdder_func())
```

______________________________________________________________________

## Formatting and linting

We use Ruff as the formatter and linter. The pre-commit has hooks which runs
checking and applies linting automatically. The CI validates the linting,
ensuring main is always looking clean.

You can manually use these commands too:

1. `make lint` - check for linting issues.
1. `make format` - fix linting issues.

______________________________________________________________________

## CICD

### Publishing to PyPI

We publish to PyPI using Github releases. Steps are as follows:

1. Manually update the version in `pyproject.toml` file using a PR and merge to
   main. Use `uv version --bump {patch/minor/major}` to update the version.
1. Create a new release in Github with the tag name as the version number. This
   will trigger the `publish` workflow. In the Release window, type in the
   version number and it will prompt to create a new tag.
1. Verify the release in
   [PyPI](https://pypi.org/project/python-package-template/)
