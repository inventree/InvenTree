---
title: Report Fonts
---

## Report Fonts

Report and label templates are rendered to PDF by [WeasyPrint](./weasyprint.md), which can only draw text using fonts that it can actually load at render time. If a template requests a font which is not available, WeasyPrint silently falls back to a default system font - the PDF will still render, but not in the expected typeface.

For example, the following CSS will *not* work unless the *Roboto* font is available to the server:

```css
body {
    font-family: 'Roboto', sans-serif;
}
```

There are three ways to make a custom font available to WeasyPrint:

| Method | Requires network access | Requires server access | Notes |
| --- | --- | --- | --- |
| [Uploaded asset file](#loading-fonts-from-asset-files) | No | No | Font is embedded into each template which uses it |
| [Remote URL](#loading-fonts-from-remote-sources) | Yes | No | Requires the *Report URL Fetching* setting to be enabled |
| [System font](#adding-fonts-to-the-docker-image) | No | Yes | Font is available to all templates by name |

### Default Fonts

The official InvenTree docker image ships with a small set of fonts pre-installed:

- [GNU FreeFont](https://www.gnu.org/software/freefont/) (`FreeSans`, `FreeSerif`, `FreeMono`)
- [Terminus](https://terminus-font.sourceforge.net/)
- [Noto](https://fonts.google.com/noto) (core fonts and CJK fonts)

These fonts can be referenced by name in any template, without any additional configuration. For a bare metal installation, the available fonts depend on what is installed on the host system.

!!! tip "List Available Fonts"
    To see which fonts are installed in the docker container, run `docker compose exec inventree-server fc-list : family`

## Loading Fonts from Asset Files

A font file (`.ttf`, `.otf`, `.woff` or `.woff2`) can be uploaded as a [report asset](./assets.md), and then embedded into a template using an `@font-face` rule. The `{% raw %}{% asset %}{% endraw %}` template tag encodes the file as a `data:` URI, so no network access is required, and this method works regardless of the [URL fetching](./index.md#url-fetching) settings.

```html
{% raw %}
{% load report %}

<head>
    <style>
        @font-face {
            font-family: 'Barlow Condensed';
            src: url('{% asset "BarlowCondensed-Regular.ttf" %}') format('truetype');
            font-weight: normal;
        }

        @font-face {
            font-family: 'Barlow Condensed';
            src: url('{% asset "BarlowCondensed-Bold.ttf" %}') format('truetype');
            font-weight: bold;
        }

        body {
            font-family: 'Barlow Condensed', sans-serif;
        }
    </style>
</head>
{% endraw %}
```

!!! info "Font Weights and Styles"
    Each weight (e.g. bold) and style (e.g. italic) of a font is typically a separate file. Declare a separate `@font-face` rule for each variant you need, otherwise WeasyPrint will synthesize bold or italic text from the regular font.

!!! tip "Use Snippets"
    If the same font is used across multiple templates, place the `@font-face` declarations in a [report snippet](./snippets.md) and include it in each template.

## Loading Fonts from Remote Sources

Fonts can be loaded from a remote URL - for example, from [Google Fonts](https://fonts.google.com/). However, by default InvenTree **blocks** all remote `http://` and `https://` requests made while rendering a template. This is a security measure, which prevents report templates from being used to make requests from the InvenTree server (refer to the [security documentation](./index.md#security) for details).

If a remote font is requested while URL fetching is disabled, the request is blocked, and the template falls back to a default font. A warning message is written to the server log.

### Enable URL Fetching

To load fonts from a remote source, a staff user must first enable the **Report URL Fetching** setting (`REPORT_FETCH_URLS`) in the *Reporting* section of the [system settings](../settings/global.md#reporting). Remote URLs are still validated against private and reserved IP ranges, so fonts can only be loaded from publicly addressable servers.

!!! warning "Enable with care"
    Enabling this setting allows *any* report template to trigger outbound HTTP requests from the InvenTree server. Where possible, prefer [uploading the font as an asset](#loading-fonts-from-asset-files) or [installing it on the server](#adding-fonts-to-the-docker-image) instead.

### Load a Font File Directly

Once URL fetching is enabled, a font file can be referenced directly in an `@font-face` rule:

```html
<head>
    <style>
        @font-face {
            font-family: 'Barlow Condensed';
            src: url('https://fonts.gstatic.com/s/barlowcondensed/v13/HTxwL3I-JCGChYJ8VI-L6OO_au7B46r2_3E.ttf') format('truetype');
        }

        body {
            font-family: 'Barlow Condensed', sans-serif;
        }
    </style>
</head>
```

### Load a Google Fonts Stylesheet

Alternatively, the stylesheet provided by Google Fonts can be imported, which declares the required `@font-face` rules automatically:

```html
<head>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@400;700&display=swap');

        body {
            font-family: 'Barlow Condensed', sans-serif;
        }
    </style>
</head>
```

!!! info "Rendering Performance"
    Remote fonts are downloaded each time a template is rendered. This makes rendering slower, and the template will fall back to a default font if the remote server cannot be reached.

## Adding Fonts to the Docker Image

Installing a font on the server makes it available to *all* templates by name, with no `@font-face` rule required and no network access at render time. WeasyPrint locates installed fonts using [fontconfig](https://www.freedesktop.org/wiki/Software/fontconfig/), which searches the `/usr/local/share/fonts/` directory inside the container.

!!! warning "Server and Worker"
    Reports and labels may be rendered by either the `inventree-server` or the `inventree-worker` container. Custom fonts must be added to **both** containers, otherwise output will be inconsistent.

### Mount a Font Directory

The simplest approach is to mount a directory of font files into the containers. Download the required font files (e.g. `.ttf` files from [Google Fonts](https://fonts.google.com/)) and place them in a directory alongside your `docker-compose.yml` file, e.g. `./fonts/`.

Then add a volume mount to both the `inventree-server` and `inventree-worker` services in your `docker-compose.yml` file:

```yaml
    inventree-server:
        # ...
        volumes:
            # Data volume must map to /home/inventree/data
            - ${INVENTREE_EXT_VOLUME}:/home/inventree/data:z
            # Custom fonts for report rendering
            - ./fonts:/usr/local/share/fonts/custom:ro,z

    inventree-worker:
        # ...
        volumes:
            # Data volume must map to /home/inventree/data
            - ${INVENTREE_EXT_VOLUME}:/home/inventree/data:z
            # Custom fonts for report rendering
            - ./fonts:/usr/local/share/fonts/custom:ro,z
```

Restart the containers to apply the changes:

```bash
docker compose down
docker compose up -d
```

Verify that the font has been detected:

```bash
docker compose exec inventree-server fc-list : family | grep -i barlow
docker compose exec inventree-worker fc-list : family | grep -i barlow
```

The font can now be referenced by its family name in any template:

```css
body {
    font-family: 'Barlow Condensed', sans-serif;
}
```

!!! tip "Font Family Name"
    The name used in the `font-family` property must match the family name reported by `fc-list`, which may differ from the file name.

### Build a Custom Image

Alternatively, fonts can be baked into a custom docker image which extends the official InvenTree image. For example, create a `Dockerfile` alongside your `docker-compose.yml` file:

```dockerfile
FROM inventree/inventree:stable

# Copy custom font files into the system font directory
COPY fonts/ /usr/local/share/fonts/custom/

# Rebuild the font cache
RUN fc-cache -f
```

Fonts packaged for Debian can also be installed using `apt-get` (the image runs as root by default):

```dockerfile
FROM inventree/inventree:stable

RUN apt-get update && apt-get install -y --no-install-recommends \
    fonts-roboto \
    && apt-get clean && rm -rf /var/lib/apt/lists/*
```

Then, update the `inventree-server` and `inventree-worker` services in `docker-compose.yml` to build from this file, rather than pulling the official image:

```yaml
    inventree-server:
        build: .
        image: inventree-custom:stable
        # ...

    inventree-worker:
        image: inventree-custom:stable
        # ...
```

!!! info "Rebuild on Upgrade"
    A custom image must be rebuilt (`docker compose build --pull`) whenever you upgrade InvenTree, to pick up the new version of the base image.

### Bare Metal Installations

For a bare metal installation, install the required fonts on the host system using the system package manager, or copy the font files into `/usr/local/share/fonts/` and run `fc-cache -f`. Restart the InvenTree server and background worker processes after installing new fonts.
