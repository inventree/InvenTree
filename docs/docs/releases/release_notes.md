---
title: Release Notes
---

## InvenTree Versioning

The InvenTree project follows a formalized release numbering scheme, according to the [semantic versioning specification](https://semver.org/).

### Stable Branch

The head of the *stable* code branch represents the most recent stable tagged release of InvenTree.

!!! info "<span class='fab fa-docker'></span> Stable Docker"
    To pull down the latest *stable* release of InvenTree in docker, use `inventree/inventree:stable`

### Development Branch

The head of the *master* code branch represents the "latest and greatest" working codebase. All features and bug fixes are merged into the master branch, in addition to relevant stable release branches.

!!! info "<span class='fab fa-docker'></span> Latest Docker"
    To pull down the latest *development* version of InvenTree in docker, use `inventree/inventree:latest`

## Stable Releases

!!! warning "Release Notes"
    Starting from version 0.12.0, release notes are now available only on the [InvenTree GitHub Releases Page](https://github.com/inventree/InvenTree/releases). Release notes for versions prior to 0.12.0 are also tagged below.

{% include "release_table_head.html" %}

{% with prefix="0.11" %}{% include "release_table.html" %}{% endwith %}
{% with prefix="0.10" %}{% include "release_table.html" %}{% endwith %}
{% with prefix="0.9" %}{% include "release_table.html" %}{% endwith %}
{% with prefix="0.8" %}{% include "release_table.html" %}{% endwith %}
{% with prefix="0.7" %}{% include "release_table.html" %}{% endwith %}
{% with prefix="0.6" %}{% include "release_table.html" %}{% endwith %}
{% with prefix="0.5" %}{% include "release_table.html" %}{% endwith %}
{% with prefix="0.4" %}{% include "release_table.html" %}{% endwith %}
{% with prefix="0.3" %}{% include "release_table.html" %}{% endwith %}
{% with prefix="0.2" %}{% include "release_table.html" %}{% endwith %}
{% with prefix="0.1" %}{% include "release_table.html" %}{% endwith %}

{% include "release_table_tail.html" %}

## Upcoming Features

In-progress and upcoming features can be viewed on [GitHub](https://github.com/inventree/inventree/pulls), where the InvenTree source code is hosted.

## Suggest Something New

To suggest a new feature (or report a bug) raise an [issue on GitHub](https://github.com/inventree/inventree/issues).
