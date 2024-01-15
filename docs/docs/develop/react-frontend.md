---
title:  Platform UI / React
---

## Setup

The new React-based UI will not be available by default. In order to set your development environment up to view the frontend, follow this guide.
The new UI requires a separate frontend server to run to serve data for the new Frontend.

### Install

The React frontend requires its own packages that aren't installed via the usual invoke tasks.

#### Docker

Run the following command:
`docker compose run inventree-dev-server invoke frontend-compile`
This will install the required packages for running the React frontend on your InvenTree dev server.

#### Devcontainer
!!! warning "This guide assumes you already have a running devcontainer"
!!! info "All these steps are performed within Visual Studio Code"

Open a new terminal from the top menu by clicking `Terminal > New Terminal`
Make sure this terminal is running within the virtual env. The start of the last line should display `(venv)`

Run the command `invoke frontend-compile`. Wait for this to finish

### Running

After finishing the install, you need to launch a frontend server to be able to view the new UI.

Using the previously described ways of running commands, execute the following:
`invoke frontend-dev` in your environment
This command does not run as a background daemon, and will occupy the window it's ran in.

### Accessing

When the frontend server is running, it will be available on port 5173.
i.e: https://localhost:5173/

### Information

On Windows, any Docker interaction is run via WSL. Naturally, all containers and devcontainers run through WSL.
The default configuration for the frontend server sets up file polling to enable hot reloading.
This is in itself a huge performance hit. If you're running an older system, it might just be enough to block anything from running in the container.

If you're having issues running the Frontend server, have a look at your Docker Desktop app.
If you routinely see the container using almost ALL available CPU capacity, you need to turn off file polling.

!!! warning "Turning off file polling requires you to restart the frontend server process upon each file change"

Head to the following path: `src/frontend/vite.config.ts` and change:

`const IS_IN_WSL = platform().includes('WSL') || release().includes('WSL');`
to
`const IS_IN_WSL = false;`

!!! tip "Make sure to not commit this change!"

!!! warning "This change will require you to restart the frontend server for every change you make in the frontend code"
