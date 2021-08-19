Contributions to InvenTree are welcomed - please follow the guidelines below.

## Feature Branches

No pushing to master! New featues must be submitted in a separate branch (one branch per feature).

## Include Migration Files

Any required migration files **must** be included in the commit, or the pull-request will be rejected. If you change the underlying database schema, make sure you run `invoke migrate` and commit the migration files before submitting the PR.


## Testing

Any new code should be covered by unit tests - a submitted PR may not be accepted if the code coverage is decreased.

## Documentation

New features or updates to existing features should be accompanied by user documentation. A PR with associated documentation should link to the matching PR at https://github.com/inventree/inventree-docs/

## Code Style

Sumbitted Python code is automatically checked against PEP style guidelines. Locally you can run `invoke style` to ensure the style checks will pass, before submitting the PR.
