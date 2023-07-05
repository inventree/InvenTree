# InvenTree Documentation

[![Documentation Status](https://readthedocs.org/projects/inventree/badge/?version=latest)](https://inventree.readthedocs.io/en/latest/?badge=latest)

This repository hosts the [official documentation](https://inventree.readthedocs.io/) for [InvenTree](https://github.com/inventree/inventree), an open source inventory management system.

To serve this documentation locally (e.g. for development), you will need to have Python 3 installed on your system.

## Setup

Run the following commands from the top-level project directory:

```
$ git clone https://github.com/inventree/inventree
$ cd inventree/docs
$ pip install -r requirements.txt
```

## Serve Locally

To serve the pages locally, run the following command (from the top-level project directory):

```
$ mkdocs serve -f docs/mkdocs.yml -a localhost:8080
```

## Edit Documentation Files

Once the server is running, it will monitor the documentation files for any changes, and update the served pages.

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

Images are served from the `./docs/assets/images` folder and can be added as follow:
```
{% with id="image_id", url="folder/image_name.png", description="Text shown if image is not loaded properly" %}
{% include 'img.html' %}
{% endwith %}
```

Replace:
* `image_id` with a short unique identifier for the image (most commonly, `image_id` is same as `image_name`)
* `folder` with the folder in `docs/assets/images` in which the image is stored
* `image_name` with the name of the image
* `.png` with the image extension (PNG or JPEG are preferred formats)

### Global variables

Refer to the [reference documentation](https://squidfunk.github.io/mkdocs-material/reference/variables/#using-custom-variables) to find out how to add global variables to the documentation site.

Global variables should be added in the `# Global Variables` section of the `mkdocs.yml` configuration file.

## Credits

This documentation makes use of the [mkdocs-material template](https://github.com/squidfunk/mkdocs-material)
