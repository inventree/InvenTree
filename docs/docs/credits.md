---
title: Credits
---

## Supporting Libraries

The InvenTree codebase relies on a number of supporting libraries:

### Backend (Server) Libraries

The InvenTree server relies on the following Python libraries:

{% with packages=config.backend_packages %}
{% include "package_table.html" %}
{% endwith %}

### Frontend (Client) Libraries

The InvenTree client relies on the following Javascript libraries:

{% with packages=config.frontend_packages %}
{% include "package_table.html" %}
{% endwith %}


## Source Code Contributions

The InvenTree project relies on the expertise and generosity of its [source code contributors](https://github.com/inventree/InvenTree/graphs/contributors).

## Translation Contributions

Translation efforts are supported by the InvenTree community. We appreciate the efforts of our [translation team](https://crowdin.com/project/inventree).
