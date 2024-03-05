---
title: Devcontainer
---

## Devcontainer

[Devcontainers](https://code.visualstudio.com/docs/devcontainers/containers) are the easiest way to get into InvenTree development. You can either run them on your machine in vscode or use github codespaces.

### Setup in vscode

#### Prerequisites

You need to make sure that you have the following tools installed before continuing.

- [git](https://git-scm.com/downloads) is needed to clone the repository
- [docker](https://www.docker.com/products/docker-desktop/) is needed to run the devcontainer
- [vscode](https://code.visualstudio.com/Download) is needed to edit and debug code

#### Docker Containers

The InvenTree devcontainer setup will install two docker containers:

| Container | Description |
| --- | --- |
| db | InvenTree database (postgresql) |
| inventree | InvenTree server |

#### Setup/Installation

1. Clone the repository (If you want to submit changes fork it and use the url to your fork in the next step)
   ```bash
   git clone https://github.com/inventree/InvenTree.git
   ```
2. Open vscode, navigate to the extensions sidebar and search for `ms-vscode-remote.remote-containers`. Click on install.
3. Open the cloned folder from above by clicking on `file > open folder`
4. vscode should now ask you if you'd like to reopen this folder in a devcontainer. Click `Reopen in Container`. If it does not ask you, open the command palette (<kbd>CTRL/CMD</kbd>+<kbd>Shift</kbd>+<kbd>P</kbd>) and search for `Reopen in Container`. This can take a few minutes until the image is downloaded, build and setup with all dependencies.
5. Open a new terminal from the top menu by clicking `Terminal > New Terminal`
6. The last line in your terminal should now show the text `(venv)` at the start of the line
7. You are done! You now should have a functioning InvenTree development installation

### Setup in Codespaces

Open [inventree/InvenTree](https://github.com/inventree/InvenTree) with your browser and click on `Code`, select the `codespaces` tab and click on create codespace on current branch. This may can take a few minutes until your inventree development environment is setup.

!!! warning "Close the terminal"
    The appearing terminal which says `Welcome to codespaces` is not using the virtual env. Close it and use a new terminal that will automatically connect to the venv for using commands.

### Running tasks

Tasks can help you executing scripts. You can run them by open the command panel (<kbd>CMD</kbd>+<kbd>Shift</kbd>+<kbd>P</kbd>) and search for `Run Task`. Then choose the desired task.

#### Setup demo dataset

If you need some demo test-data, run the `setup-test` task. This will import an `admin` user with the password `inventree`. For more info on what this dataset contains see [inventree/demo-dataset](https://github.com/inventree/demo-dataset).

#### Setup a superuser

If you only need a superuser, run the `superuser` task. It should prompt you for credentials.

#### Run background workers

If you need to process your queue with background workers, run the `worker` task. This is a foreground task which will execute in the terminal.

### Running InvenTree

You can either only run InvenTree or use the integrated debugger for debugging. Goto the `Run and debug` side panel make sure `InvenTree Server` is selected. Click on the play button on the left.

!!! tip "Debug with 3rd party"
    Sometimes you need to debug also some 3rd party packages. Just select `InvenTree Servre - 3rd party`

You can now set breakpoints and vscode will automatically pause execution if that point is hit. You can see all variables available in that context and evaluate some code with the debugger console at the bottom. Use the play or step buttons to continue execution.

!!! info "React Frontend development"

The React frontend requires additional steps to run. Refer to [Platform UI / React](./react-frontend.md)

### Plugin development

The easiest way for plugin developing is by using the InvenTree devcontainer. Just mount your plugin repository also into the devcontainer workspace and install it as pip editable package.

1. To mount your plugin repo into the workspace, add this to your `.devcontainer/devcontainer.json` file. (Make sure that you don't commit it)
   ```json
   "mounts": [
     "source=/path/to/your/local/inventree-plugin,target=/workspaces/inventree-plugin,type=bind,consistency=cached"
   ],
   ```
2. Add `/workspaces/inventree-plugin` to your vscode workspace folders by click on `File > Add folder to workspace…`.
3. Install your plugin as pip editable install by executing the following command in the venv.
   ```bash
   pip install -e /workspaces/inventree-plugin
   ```
4. Add InvenTree core code to Pylance IntelliSense path by adding the following file to your plugin repo `.vscode/settings.json` (Your path can be different depending on your setup):
   ```json
   {
     "python.analysis.extraPaths": ["/workspaces/InvenTree/InvenTree"]
   }
   ```

Your plugin should now be activateable from the InvenTree settings. You can also use breakpoints for debugging.

### Troubleshooting

#### Your ssh-keys are not available in the devcontainer but are loaded to the active `ssh-agent` on macOS

Make sure you enabled full disk access on macOS for vscode, otherwise your ssh-keys are not available inside the container (Ref: [Automatically add SSH keys to ssh-agent [comment]](https://github.com/microsoft/vscode-remote-release/issues/4024#issuecomment-831671081)).

#### You're not able to use your gpg-keys inside the devcontainer to sign commits on macOS

Make sure you have `gnupg` and `pinentry-mac` installed and set up correctly. Read this [medium post](https://medium.com/@jma/setup-gpg-for-git-on-macos-4ad69e8d3733) for more info on how to set it up correctly.

#### Where are the database, media files, ... stored?

Backups, Commandhistory, media/static files, venv, plugin.txt, secret_key.txt, ... are stored in the `dev` folder. If you want to start with a clean setup, you can remove that folder, but be aware that this will delete everything you already setup in InvenTree.

### Performance Improvements

If you are running a devcontainer in Windows, you may experience some performance issues - particularly related to file system operations.

For a significant improvement in performance, the source code should be installed into the **WSL 2** filesystem (not on your "Windows" filesystem). This will greatly improve file access performance, and also make the devcontainer much more responsive to file system changes.

You can also refer to the [Improve disk performance guide](https://code.visualstudio.com/remote/advancedcontainers/improve-performance) for more information.
