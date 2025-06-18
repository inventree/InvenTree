---
title: React Frontend Development
---

## Setup

The following documentation details how to setup and run a development installation of the InvenTree frontend user interface. It is assumed that you are using the [InvenTree devcontainer setup](./devcontainer.md).

!!! warning "This guide assumes you already have a running devcontainer"

!!! info "All these steps are performed within Visual Studio Code"

!!! note "Devcontainer"
    The [devcontainer](./devcontainer.md) setup already includes all prerequisite packages, and is ready to run the frontend server.

### Install Packages

First, ensure that all the required frontend packages are installed:

```bash
invoke int.frontend-install
```

## Server Processes

The development environment requires two server processes to be running -  the backend server and the frontend server.

### Backend Server

Ensure that the backend server is running, before launching the frontend server. The backend server is responsible for serving the API endpoints that the frontend will connect to.

```bash
invoke dev.server
```

This will launch the backend server in the foreground, and will occupy the terminal window it is run in.

### Frontend Server

Now that the backend server is running, you can launch the frontend server. The frontend server is responsible for serving the React-based user interface, and provides a development environment for building and testing the frontend code.

In a *separate terminal window*, run the following command to start the frontend server:

```bash
invoke dev.frontend-server
```

When the frontend server is running, it will be available at https://localhost:5173/

## Live Reloading

Any changes made to the frontend code will automatically trigger a live reload of the frontend server. This means that you can make changes to the code, and see the results immediately in your browser without needing to manually refresh the page.

## Debugging

You can attach the vscode debugger to the frontend server to debug the frontend code. With the frontend server running, open the `Run and Debug` view in vscode and select `InvenTree Frontend - Vite` from the dropdown. Click the play button to start debugging. This will attach the debugger to the running vite server, and allow you to place breakpoints in the frontend code.

!!! info "Backend Server"
    To debug the frontend code, the backend server must be running (in a separate process). Note that you cannot debug the backend server and the frontend server in the same vscode instance.


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

This will first launch the backend server (at http://localhost:8000), and then run the tests against the frontend server (at http://localhost:5173). An interactive browser window will open, and you can run the tests individually or as a group.

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

## Tips and Tricks

### WSL

On Windows, any Docker interaction is run via WSL. Naturally, all containers and devcontainers run through WSL.
The default configuration for the frontend server sets up file polling to enable hot reloading.
This is in itself a huge performance hit. If you're running an older system, it might just be enough to block anything from running in the container.

If you're having issues running the Frontend server, have a look at your Docker Desktop app.
If you routinely see the container using almost ALL available CPU capacity, you need to turn off file polling.

!!! warning "Turning off file polling requires you to restart the frontend server process upon each file change"

Head to the following path: `src/frontend/vite.config.ts` and change:

```const IS_IN_WSL = platform().includes('WSL') || release().includes('WSL');```

to

```const IS_IN_WSL = false;```

!!! tip "Make sure to not commit this change to Git!"

!!! warning "This change will require you to restart the frontend server for every change you make in the frontend code"

### Caveats

When running the frontend development server, some features may not work entirely as expected! Please take the time to understand the flow of data when running the frontend development server, and how it interacts with the backend server!

#### SSO Login

When logging into the frontend dev server via SSO, the redirect URL may not redirect correctly.
