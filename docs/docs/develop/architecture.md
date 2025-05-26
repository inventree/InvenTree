---
title: Architecture
---

## Project Overview

TODO Describes the components of the ecosystem.

Sample flow chart

``` mermaid
graph LR
  A[Start] --> B{Error?};
  B -->|Yes| C[Hmm...];
  C --> D[Debug];
  D --> B;
  B ---->|No| E[Yay!];
```

TODO And more text

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

### Backend Architecture

TODO Describes the python/django designs

### Frontend Architecture

TODO Describes how frontend calls works.

## Security

TODO Security aspects of the architecture and SDLC

### Assurances
