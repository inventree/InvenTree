---
title: Getting started
---

InvenTree consists of a Django-based backend server, and a HTML / vanilla JS based frontend that uses Bootstrap. The main languages used are Python and Javascript.
As part of the larger project other languages/techniques are used, such as docker (dev/deployment), bash (installer) and markdown (documentation).

### Getting started
#### Getting to know the basics

The Django framework is a powerful tool for creating web applications. It is well documented and has a large community. The [Django documentation](https://docs.djangoproject.com/en/stable/) is a good place to start.

In particular the [tutorial](https://docs.djangoproject.com/en/stable/intro/tutorial01/) is a good way to get to know the basics of Django.
InvenTree follows the best practies for Django so most of the contents should be applicable to InvenTree as well. The REST API is based on the [Django REST framework](https://www.django-rest-framework.org/).

#### Setting up a development environment

The recommended way to set up a development environment is to use VSCode devcontainers. The required files are provided with the repo, the docs are on a [dedicated page](./devcontainer.md).

It is also possible to use [docker development](../start/docker_dev.md) or [bare metal development](../start/bare_dev.md). With these you need to install the required dependencies manually with a dedicated task.
```bash
invoke setup-dev
```

#### Following standards

Before contributing to the project, please read the [contributing guidelines](contributing.md). Pull requests that do not follow the guidelines, do not pass QC checks or lower the test coverage will not be accepted.
