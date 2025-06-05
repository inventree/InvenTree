---
title: Architecture
---

## Project Overview

TODO Describes the components of the ecosystem.


## Typical Deployment

InvenTree is a classical Django Application and supports the WSGI interface standard. The following diagram shows a typical and recommended deployment architecture of InvenTree.

``` mermaid
flowchart LR
    Request --- RP[1: Reverse Proxy]
    RP --- Gunicorn[5: Gunicorn]
    subgraph image:inventree/inventree
    Gunicorn --- Django[6: Django Server processes]
    end
    Django --- Database@{ shape: cyl, label: "SQL Database" }
    Django --- Redis
    Worker[7: Q2 Worker] ---  Redis@{ shape: cyl, label: "9: Redis Cache" }
      Database -- 8: DB holds tasks ---> Worker

    subgraph caddy
    RP --- file[2: file server]
end

    file --- s[3: Static Files]
    file --- m[Media Files]
    RP-. 4: API auth request .-> Gunicorn
```

1. A Request is received by a reverse proxy (e.g. Caddy, Nginx, Apache).
2. Requests for static or media files are either served directly by the reverse proxy or forwarded to a dedicated file server
3. Static or media files can be served by the different file server (placing static files in a CDN for example)
4. Media files require an API authentication request to the Django server to ensure the user has access to the file
5. API or frontend requests are forwarded from the reverse proxy to Gunicorn, which is a WSGI server that handles server Django processes.
6. The Gunicorn processes are loosely coubled instances of Django application - which mainly serves a REST API as the frontend only needs a few full django calls (see [frontend architecture](#frontend-architecture) below).
7. A properly configured InvenTree instance will also run background workers (Q2 Worker) which are responsible for processing long-running tasks, such as sending notifications, generating reports or calculating expensive updates. Q2 is used as the task processing library, which runs multiple loosely coupled worker processes.
8. The database holds tasks and is queried by the workers. This enables relatively durable task processing, as the underlying server can be restarted with minimal task loss.
9. Various components of InvenTree can benefit from a Redis or protocol compatible cache, which is used to store frequently accessed data, such as user sessions, API tokens, global or plugin settings, or other transient data. This can help to improve performance and reduce load on the database.

## Code Architecture

This sections describes various architectural aspects of the InvenTree codebase and mechanisms and lifecycles in the system.

Knowledege of these aspects is not required to use InvenTree, but it is helpful for developers who want to contribute to the project or to understand where / how one might extend the system with plugins or by pathching in custom functionality.

### Repository layout and separation of concerns

All code that is intended to be executed on the server is located in the `src/` directory. Some code in contrib might be needed to deploy or maintain an instance.
One exception is the `tasks.py` file, that contains definitions for various maintenance tasks that can be run from the command line. This file is located in the root directory of the repository to make instructions easier.

Code styles are generally only applied to the code in the `src/` directory.

### Backend Architecture

InvenTree's backend is a Django application. It is generally structured in a way that follows Django's conventions, but also includes some customizations and extensions to support the specific needs of InvenTree.
Most remarkable deviations from the Django standard are:
- Manipulation of the django app mechanisms to enable the [plugin system](#plugin-system)
- Usage of a custom role-mapping system to make permissions more approachable

The backend aims to be:
- API first, with a RESTful API that is used by the frontend and can also be used by other applications.
- Modular, with a clear separation of concerns between different components and apps.
- Tested reasonably throughout with transparent test coverage
- Following the Django and generally accepted security conventions

#### Configuration sources

#### Middlewares and templateting

#### Built-in apps

#### Plugin system

### Frontend Architecture

InvenTree's frontend is primarily a single-page application (SPA) built with React.

#### Coupling to the backend

#### Translations

#### Library / exported components

## Security

TODO Security aspects of the architecture and SDLC

### Assurances
