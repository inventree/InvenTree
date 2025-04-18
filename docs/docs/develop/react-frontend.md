---
title: React Frontend Development
---

## Setup

The following documentation details how to setup and run a development installation of the InvenTree frontend user interface.

### Prerequisites

To run the frontend development server, you will need to have the following installed:

- Node.js
- Yarn

!!! note "Devcontainer"
    The [devcontainer](./devcontainer.md) setup already includes all prerequisite packages, and is ready to run the frontend server.

### Install

The React frontend requires its own packages that aren't installed via the usual [invoke](../start/invoke.md) tasks.

#### Docker

Run the following command:
`docker compose run inventree-dev-server invoke int.frontend-compile`
This will install the required packages for running the React frontend on your InvenTree dev server.

#### Devcontainer

!!! warning "This guide assumes you already have a running devcontainer"

!!! info "All these steps are performed within Visual Studio Code"

Open a new terminal from the top menu by clicking `Terminal > New Terminal`
Make sure this terminal is running within the virtual env. The start of the last line should display `(venv)`

Run the command `invoke int.frontend-compile`. Wait for this to finish

### Running

After finishing the install, you need to launch a frontend server to be able to view the new UI.

Using the previously described ways of running commands, execute the following:
`invoke dev.frontend-server` in your environment
This command does not run as a background daemon, and will occupy the window it's ran in.

### Accessing

When the frontend server is running, it will be available on port 5173.
i.e: https://localhost:5173/

!!! note "Backend Server"
    The InvenTree backend server must also be running, for the frontend interface to have something to connect to! To launch a backend server, use the `invoke dev.server` command.

### Debugging

You can attach the vscode debugger to the frontend server to debug the frontend code. With the frontend server running, open the `Run and Debug` view in vscode and select `InvenTree Frontend - Vite` from the dropdown. Click the play button to start debugging. This will attach the debugger to the running vite server, and allow you to place breakpoints in the frontend code.

!!! info "Backend Server"
    To debug the frontend code, the backend server must be running (in a separate process). Note that you cannot debug the backend server and the frontend server in the same vscode instance.

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

### Caveats

When running the frontend development server, some features may not work entirely as expected! Please take the time to understand the flow of data when running the frontend development server, and how it interacts with the backend server!

#### SSO Login

When logging into the frontend dev server via SSO, the redirect URL may not redirect correctly.

## Testing

The frontend codebase it tested using [Playwright](https://playwright.dev/). There are a large number of tests that cover the frontend codebase, which are run automatically as part of the CI pipeline.

### Install Playwright

To install the required packages to run the tests, you can use the following commands:

```bash
cd src/frontend
sudo npx playwright install-deps
npx playwright install
```

### Running Tests

To run the tests locally, in an interactive editor, you can use the following command:

```bash
cd src/frontend
npx playwright test --ui
```

This will first launch the backend server (at `http://localhost:8000`), and then run the tests against the frontend server (at `http://localhost:5173`). An interactive browser window will open, and you can run the tests individually or as a group.

### Viewing Reports

The playwright tests are run automatically as part of the project's CI pipeline, and the results are stored as a downloadable report. The report file can be "replayed" using playwright, to view the results of the test run, as well as closely inspect any failed tests.

To view the report, you can use the following command, after downloading the report and extracting from the zipped file:

```bash
npx playwright show-report path/to/report
```

### No Tests Found

If there is any problem in the testing launch sequence, the playwright UI will display the message "No Tests". In this case, an error has occurred, likely launching the InvenTree server process (which runs in the background).

To debug this situation, and determine what error needs to be resolved, run the following command:

```bash
npx playwright test --debug
```

This will print out any errors to the console, allowing you to resolve issues before continuing. In all likelihood, your InvenTree installation needs to be updated, and simply running `invoke update` will allow you to continue.
