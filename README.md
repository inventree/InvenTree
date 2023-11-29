<div align="center">
  <img src="assets/images/logo/inventree.png" alt="InvenTree logo" width="200" height="auto" />
  <h1>InvenTree</h1>
  <p>Open Source Inventory Management System </p>

<!-- Badges -->
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)![GitHub tag (latest SemVer)](https://img.shields.io/github/v/tag/inventree/inventree)
![CI](https://github.com/inventree/inventree/actions/workflows/qc_checks.yaml/badge.svg)
[![Documentation Status](https://readthedocs.org/projects/inventree/badge/?version=latest)](https://inventree.readthedocs.io/en/latest/?badge=latest)
![Docker Build](https://github.com/inventree/inventree/actions/workflows/docker.yaml/badge.svg)
[![OpenSSF Best Practices](https://bestpractices.coreinfrastructure.org/projects/7179/badge)](https://bestpractices.coreinfrastructure.org/projects/7179)
[![Netlify Status](https://api.netlify.com/api/v1/badges/9bbb2101-0a4d-41e7-ad56-b63fb6053094/deploy-status)](https://app.netlify.com/sites/inventree/deploys)
[![DeepSource](https://app.deepsource.com/gh/inventree/InvenTree.svg/?label=active+issues&show_trend=false&token=trZWqixKLk2t-RXtpSIAslVJ)](https://app.deepsource.com/gh/inventree/InvenTree/)

[![Coveralls](https://img.shields.io/coveralls/github/inventree/InvenTree)](https://coveralls.io/github/inventree/InvenTree)
[![Crowdin](https://badges.crowdin.net/inventree/localized.svg)](https://crowdin.com/project/inventree)
![GitHub commit activity](https://img.shields.io/github/commit-activity/m/inventree/inventree)
[![Docker Pulls](https://img.shields.io/docker/pulls/inventree/inventree)](https://hub.docker.com/r/inventree/inventree)

![GitHub Org's stars](https://img.shields.io/github/stars/inventree?style=social)
[![Twitter Follow](https://img.shields.io/twitter/follow/inventreedb?style=social)](https://twitter.com/inventreedb)
[![Subreddit subscribers](https://img.shields.io/reddit/subreddit-subscribers/inventree?style=social)](https://www.reddit.com/r/InvenTree/)


<h4>
    <a href="https://demo.inventree.org/">View Demo</a>
  <span> · </span>
    <a href="https://docs.inventree.org/en/latest/">Documentation</a>
  <span> · </span>
    <a href="https://github.com/inventree/InvenTree/issues/new?template=bug_report.md&title=[BUG]">Report Bug</a>
  <span> · </span>
    <a href="https://github.com/inventree/InvenTree/issues/new?template=feature_request.md&title=[FR]">Request Feature</a>
  </h4>
</div>

<!-- About the Project -->
## :star2: About the Project

InvenTree is an open-source Inventory Management System which provides powerful low-level stock control and part tracking. The core of the InvenTree system is a Python/Django database backend which provides an admin interface (web-based) and a REST API for interaction with external interfaces and applications. A powerful plugin system provides support for custom applications and extensions.

Check out [our website](https://inventree.org) for more details.

<!-- Roadmap -->
### :compass: Roadmap

Want to see what we are working on? Check out the [roadmap tag](https://github.com/inventree/InvenTree/issues?q=is%3Aopen+is%3Aissue+label%3Aroadmap) and [horizon milestone](https://github.com/inventree/InvenTree/milestone/42).

<!-- Integration -->
### :hammer_and_wrench: Integration

InvenTree is designed to be **extensible**, and provides multiple options for **integration** with external applications or addition of custom plugins:

* [InvenTree API](https://docs.inventree.org/en/latest/api/api/)
* [Python module](https://docs.inventree.org/en/latest/api/python/python/)
* [Plugin interface](https://docs.inventree.org/en/latest/extend/plugins)
* [Third party tools](https://docs.inventree.org/en/latest/extend/integrate)

<!-- TechStack -->
### :space_invader: Tech Stack

<details>
  <summary>Server</summary>
  <ul>
    <li><a href="https://www.python.org/">Python</a></li>
    <li><a href="https://www.djangoproject.com/">Django</a></li>
    <li><a href="https://www.django-rest-framework.org/">DRF</a></li>
    <li><a href="https://django-q.readthedocs.io/">Django Q</a></li>
    <li><a href="https://django-allauth.readthedocs.io/">Django-Allauth</a></li>
  </ul>
</details>

<details>
<summary>Database</summary>
  <ul>
    <li><a href="https://www.postgresql.org/">PostgreSQL</a></li>
    <li><a href="https://www.mysql.com/">MySQL</a></li>
    <li><a href="https://www.sqlite.org/">SQLite</a></li>
    <li><a href="https://redis.io/">Redis</a></li>
  </ul>
</details>

<details>
  <summary>Client</summary>
  <ul>
    <li><a href="https://getbootstrap.com/">Bootstrap</a></li>
    <li><a href="https://jquery.com/">jQuery</a></li>
    <li><a href="https://bootstrap-table.com/">Bootstrap-Table</a></li>
  </ul>
</details>

<details>
<summary>DevOps</summary>
  <ul>
    <li><a href="https://hub.docker.com/r/inventree/inventree">Docker</a></li>
    <li><a href="https://crowdin.com/project/inventree">Crowdin</a></li>
    <li><a href="https://coveralls.io/github/inventree/InvenTree">Coveralls</a></li>
    <li><a href="https://app.deepsource.com/gh/inventree/InvenTree">DeepSource</a></li>
    <li><a href="https://packager.io/gh/inventree/InvenTree">Packager.io</a></li>
  </ul>
</details>

<!-- Getting Started -->
## 	:toolbox: Deployment / Getting Started

There are several options to deploy InvenTree.

<div align="center"><h4>
    <a href="https://docs.inventree.org/en/latest/start/docker/">Docker</a>
    <span> · </span>
    <a href="https://inventree.org/digitalocean"><img src="https://www.deploytodo.com/do-btn-blue-ghost.svg" alt="Deploy to DO" width="auto" height="40" /></a>
    <span> · </span>
    <a href="https://docs.inventree.org/en/latest/start/install/">Bare Metal</a>
</h4></div>

Single line install - read [the docs](https://docs.inventree.org/en/latest/start/installer/) for supported distros and details about the function:
```bash
wget -qO install.sh https://get.inventree.org && bash install.sh
```

Refer to the [getting started guide](https://docs.inventree.org/en/latest/start/install/) for a full set of installation and setup instructions.

<!-- Mobile App -->
## 	:iphone: Mobile App

InvenTree is supported by a [companion mobile app](https://docs.inventree.org/en/latest/app/app/) which allows users access to stock control information and functionality.

<div align="center"><h4>
    <a href="https://play.google.com/store/apps/details?id=inventree.inventree_app">Android Play Store</a>
     <span> · </span>
    <a href="https://apps.apple.com/au/app/inventree/id1581731101#?platform=iphone">Apple App Store</a>
</h4></div>

<!-- Contributing -->
## :wave: Contributing

Contributions are welcomed and encouraged. Please help to make this project even better! Refer to the [contribution page](CONTRIBUTING.md).

<!-- Translation -->
## :scroll: Translation

Native language translation of the InvenTree web application is [community contributed via crowdin](https://crowdin.com/project/inventree). **Contributions are welcomed and encouraged**.

<!-- Sponsor -->
## :money_with_wings: Sponsor

If you use InvenTree and find it to be useful, please consider [sponsoring the project](https://github.com/sponsors/inventree).

<!-- Acknowledgments -->
## :gem: Acknowledgements

We would like to acknowledge a few special projects:
 - [PartKeepr](https://github.com/partkeepr/PartKeepr) as a valuable predecessor and inspiration
 - [Readme Template](https://github.com/Louis3797/awesome-readme-template) for the template of this page

Find a full list of used third-party libraries in [our documentation](https://docs.inventree.org/en/latest/credits/).

## :heart: Support

<p>This project is supported by the following sponsors:</p>

<p align="center">
<!-- sponsors --><a href="https://github.com/MartinLoeper"><img src="https://github.com/MartinLoeper.png" width="60px" alt="Martin Löper" /></a><a href="https://github.com/lippoliv"><img src="https://github.com/lippoliv.png" width="60px" alt="Oliver Lippert" /></a><a href="https://github.com/lfg-seth"><img src="https://github.com/lfg-seth.png" width="60px" alt="Seth Smith" /></a><a href="https://github.com/snorkrat"><img src="https://github.com/snorkrat.png" width="60px" alt="" /></a><!-- sponsors -->
</p>

<p>With ongoing resources provided by:</p>

<p align="center">
  <a href="https://inventree.org/digitalocean">
    <img src="https://opensource.nyc3.cdn.digitaloceanspaces.com/attribution/assets/SVG/DO_Logo_horizontal_blue.svg" width="201px">
  </a>
  <a href="https://www.netlify.com"> <img src="https://www.netlify.com/v3/img/components/netlify-color-bg.svg" alt="Deploys by Netlify" /> </a>
  <a href="https://crowdin.com"> <img src="https://crowdin.com/images/crowdin-logo.svg" alt="Crowdin" /> </a>
</p>


<!-- License -->
## :warning: License

Distributed under the [MIT](https://choosealicense.com/licenses/mit/) License. See [LICENSE.txt](https://github.com/inventree/InvenTree/blob/master/LICENSE) for more information.
