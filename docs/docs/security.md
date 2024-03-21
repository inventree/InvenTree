# InvenTree's commitment to security

The InvenTree project is committed to providing a secure and safe environment for all users. We know that many of our users rely on InvenTree to manage the inventory and manufacturing for their small and mid-size businesses, and we take that responsibility seriously.

To that end, we have implemented a number of security measures over the years, which we will outline in this document.

## Organisational security

The InvenTree project is managed by a small team of developers, who are responsible for the ongoing development and maintenance of the software. Two geographically distributed users have administrative access to the InvenTree codebase. Merges are only done by one of these two users, the maintainer Oliver.
InvenTree is open-source, and we welcome contributions from the community. However, all contributions are reviewed and scrutanisied before being merged into the codebase.

We provide a written [Security Policy](https://github.com/inventree/InvenTree/blob/master/SECURITY.md) in our main repo to ensure that all security issues are handled in a timely manner.

If we become aware of a security issue, we will take immediate action to address the issue, and will provide a public disclosure of the issue once it has been resolved. We support assigning CVEs to security issues where appropriate. Our past security advisories can be found [here](https://github.com/inventree/InvenTree/security/advisories)

## Technical security

The InvenTree project is hosted on GitHub, and we rely on the security measures provided by GitHub to protect the codebase.
Among those are:
- Short-lived tokens where possible
- Usage of GitHub Actions for CI/CD
- Dependabot for automated dependency updates / alerts
- Pinning dependencies to specific versions - aiming for complete reproduceability of builds
- (Optional but encouraged) Two-factor authentication for user accounts
- (Optional but encouraged) Signed commits / actions

We enforce style and security checks in our CI/CD pipeline, and we have a number of automated tests to ensure that the codebase is secure and functional. Checks are run on every pull request, and we require that all checks pass before a pull request can be merged.

InvenTree is built using the Django framework, which has a strong focus on security. We follow best practices for Django development, and we are committed to keeping the codebase up-to-date with the latest security patches and within supported versions.

We run coverage tests on our codebase to ensure that we have a high level of test coverage above 90%. This is public and can be found [here](https://coveralls.io/github/inventree/InvenTree).

## Best practices

We follow most of GitHubs community best practices, check our compilance [here](https://github.com/inventree/InvenTree/community).

We also follow OpenSSF recommodations where applicable and take part in multipbe of their security efforts:
- OSSF Best Practices, currently at a [level of passing](https://www.bestpractices.dev/de/projects/7179)
- OSSF Scorecard, running with each merge [check current state](https://securityscorecards.dev/viewer/?uri=github.com/inventree/InvenTree)
