# InvenTree Documentation

[![Documentation Status](https://readthedocs.org/projects/inventree/badge/?version=latest)](https://inventree.readthedocs.io/en/latest/?badge=latest)

This repository hosts the [official documentation](https://inventree.readthedocs.io/) for [InvenTree](https://github.com/inventree/inventree), an open source inventory management system.

## Prerequisites

InvenTree uses [MkDocs](https://www.mkdocs.org/) to convert [Markdown](https://www.mkdocs.org/user-guide/writing-your-docs/#writing-with-markdown) format `.md` files into HTML suitable for viewing in a web browser.

!!! info "Prerequisites"
    To build and serve this documentation locally (e.g. for development), you will need:

    * Python 3 installed on your system.
    * An existing InvenTree installation containing the virtual environment that was created during installation.

    These instructions assume you followed the [InvenTree bare metal installation instructions](./docs/start/install.md), so you'll have an `inventree` user, a home directory at `/home/inventree`, the InvenTree source code cloned from [GitHub](https://github.com/inventree/inventree) into `/home/inventree/src`, and a virtual environment at `/home/inventree/env`.  If you installed InvenTree some other way, this might vary, and you'll have to adjust these instructions accordingly.

!!! warning "Your InvenTree install will be updated!"
    Some of the commands that follow will make changes to your install, for example, by running any pending database migrations.  There's a small risk this may cause issues with your existing installation.  If you can't risk this, consider setting up a separate InvenTree installation specifically for documentation development.

## Building the documentation locally

To build the documentation locally, run these commands as the `inventree` user:

```
$ cd /home/inventree
$ source env/bin/activate
```

!!! info "(env) prefix"
    The shell prompt should now display the `(env)` prefix, showing that you are operating within the context of the python virtual environment

You can now install the additional packages needed by mkdocs:

```
$ cd src
$ pip install --require-hashes -r docs/requirements.txt
```

## Build Documentation

Before serving the documentation, you will need to build the API schema files from the source code, so they can be included in the documentation:

```
invoke build-docs
```

!!! tip
    This command is only required when building the documentation for the first time, or when changes have been made to the API schema.

## Serve Local files

```
$ invoke build-docs
```

You will see output similar to this (truncated for brevity):
```
Running InvenTree database migrations...
Exporting definitions...
Exporting settings definition to '/home/inventree/src/docs/generated/inventree_settings.json'...
Exported InvenTree settings definitions to '/home/inventree/src/docs/generated/inventree_settings.json'
Exported InvenTree tag definitions to '/home/inventree/src/docs/generated/inventree_tags.yml'
Exported InvenTree filter definitions to '/home/inventree/src/docs/generated/inventree_filters.yml'
Exported InvenTree report context definitions to '/home/inventree/src/docs/generated/inventree_report_context.json'
Exporting definitions complete
Exporting schema file to '/home/inventree/src/docs/generated/schema.yml'

Schema export completed: /home/inventree/src/docs/generated/schema.yml
Documentation build complete, but mkdocs not requested
```

If that worked, you can now generate the HTML format documentation pages:

```
$ mkdocs build -f docs/mkdocs.yml
```

## Viewing the generated output

To view the documentation locally, run the following command to start the MkDocs webpage server:

```
$ mkdocs serve -f docs/mkdocs.yml -a localhost:8080
```

Alternatively, you can use the `invoke` command:

```
invoke dev.docs-server
```

To see all the available options:

```
invoke dev.docs-server --help
```

You can then point your web browser at http://localhost:8080/

## Editing the Documentation Files

Once the server is running, it will monitor the documentation files for any changes, and regenerate the HTML pages.

### Admonitions

"Admonition" blocks can be added as follow:
```
!!! info "This is the admonition block title"
    This is the admonition block content
```

Refer to the [reference documentation](https://squidfunk.github.io/mkdocs-material/reference/admonitions/) to customize the admonition block to the use-case (eg. warning, missing, info, etc.).

### Internal Links

Links to internal documentation pages **must** use relative pathing, otherwise the link will be broken by the readthedocs URL formatting.

Also, linking to an internal page must use the `.md` suffix!

For example, to link to the page `/part/views` from `/stock/stocktake`, the link must be formed as follows:

```
Click [here](../part/views.md)
```

*Formatting the link as follows:*

```
Click [here](/part/views)
```

*will result in a broken link.*

### Images

Images are served from the `./docs/assets/images` folder and can be added as follows:

```
{{ image("image_name.png", base="subfolder", title="Image title") }}
```

See the `image` macro in `./docs/main.py` for more information.

### Icons

Icons can be rendered (using the [tabler icon set](https://tabler.io/icons)) as follows:

```
{{ icon("brand-github", color="red")}}
```

See the `icon` macro in `./docs/main.py` for more information.


### Global variables

Refer to the [reference documentation](https://squidfunk.github.io/mkdocs-material/reference/variables/#using-custom-variables) to find out how to add global variables to the documentation site.

Global variables should be added in the `# Global Variables` section of the `mkdocs.yml` configuration file.

## Credits

This documentation makes use of the [mkdocs-material template](https://github.com/squidfunk/mkdocs-material)
