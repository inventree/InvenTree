
The InvenTree project is committed to providing a secure and safe environment for all users. We know that many of our users rely on InvenTree to manage the inventory and manufacturing for their small and mid-size businesses, and we take that responsibility seriously.

!!! tip "This page covers the InvenTree project"
    This page covers the InvenTree project as a whole. Specific security measures for deploying your own instance of InvenTree can be found on the [Threat Model](./concepts/threat_model.md) page.

To that end, we have implemented a number of security measures over the years, which we will outline in this document.

## Organisational measures

The InvenTree project is managed by a small team of developers, who are responsible for the ongoing development and maintenance of the software. Two geographically distributed users have administrative access to the InvenTree codebase. Merges are only done by one of these two users, the maintainer Oliver.
Read the Project [Governance](./project/governance.md) document for more information.

InvenTree is open-source, and we welcome contributions from the community. However, all contributions are reviewed and scrutinised before being merged into the codebase.

### Security Policy

The official [Security Policy]({{ sourcefile("SECURITY.md") }}) is available in the code repository.
We provide this document in our main repo to increase discoverabiltity to ensure that all security issues are handled in a timely manner.

### Past Reports
If we become aware of a security issue, we will take immediate action to address the issue, and will provide a public disclosure of the issue once it has been resolved. We support assigning CVEs to security issues where appropriate.  Our [past security advisories can be found here](https://github.com/inventree/InvenTree/security/advisories).

## Technical measures

### Code hosting

The InvenTree project is hosted on GitHub, and we rely on the security measures provided by GitHub to help protect the integrity of the codebase.

Among those are:

- Short-lived tokens where possible
- Dependabot for automated dependency updates / alerts
- Integrated security reporting
- (Optional but encouraged) Two-factor authentication for user accounts
- (Optional but encouraged) Signed commits / actions

### Code style

We enforce style and security checks in our CI/CD pipeline, and we have several automated tests to ensure that the codebase is secure and functional.
Checks are run on every pull request, and we require that all checks pass before a pull request can be merged.

### Current versions

InvenTree is built using the Django framework, which has a strong focus on security. We follow best practices for Django development, and we are committed to keeping the codebase up-to-date with the latest security patches and within supported versions.

### Test coverage

We run coverage tests on our codebase to ensure that we have a high level of test coverage above 90%. This is public and can be found [here](https://app.codecov.io/gh/inventree/InvenTree).

### Pinning dependencies

We are pinning dependencies to specific versions - aiming for complete reproducibility of builds - wherever possible. Combined with continuous OSV checks, we are able to react quickly to security issues in our dependencies.

## Best practices

We follow most of GitHubs community best practices, check our compliance [here](https://github.com/inventree/InvenTree/community).

We also follow OpenSSF recommendations where applicable and take part in multiple of their security efforts:

- OSSF Best Practices, currently at a [level of passing](https://www.bestpractices.dev/de/projects/7179)
- OSSF Scorecard, running with each merge [check current state](https://securityscorecards.dev/viewer/?uri=github.com/inventree/InvenTree)

## Hall of Fame

We are grateful for all reports. Confirmed reports can be rewarded with a mention in the Hall of Fame below if the reporter requests it. We are also happy to provide a CVE if applicable.
