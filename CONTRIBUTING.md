### Contributing to InvenTree

Hi there, thank you for your interest in contributing!
Please read our contribution guidelines, before submitting your first pull request to the InvenTree codebase.

### Project File Structure

The InvenTree project is split into two main components: frontend and backend. This source is located in the `src` directory. All other files are used for project management, documentation, and testing.

```bash
InvenTree/
├─ .devops/                            # Files for Azure DevOps
├─ .github/                            # Files for GitHub
│  ├─ actions/                         # Reused actions
│  ├─ ISSUE_TEMPLATE/                  # Templates for issues and pull requests
│  ├─ workflows/                       # CI/CD flows
│  ├─ scripts/                         # CI scripts
├─ .vscode/                            # Settings for Visual Code IDE
├─ assets/                             # General project assets
├─ contrib/                            # Files needed for deployments
│  ├─ container/                       # Files related to building container images
│  ├─ installer/                       # Files needed to build single-file installer
│  ├─ packager.io/                     # Files needed for Debian/Ubuntu packages
├─ docs/                               # Directory for documentation / General helper files
│  ├─ ci/                              # CI for documentation
│  ├─ docs/                            # Source for documentation
├─ src/                                # Source for application
│  ├─ backend/                         # Directory for backend parts
│  │  ├─ InvenTree/                    # Source for backend
│  │  ├─ requirements.txt              # Dependencies for backend
│  │  ├─ package.json                  # Dependencies for backend HTML linting
│  ├─ frontend/                        # Directory for frontend parts
│  │  ├─ src/                          # Source for frontend
│  │  │  ├─ main.tsx                   # Entry point for frontend
│  │  ├─ tests/                        # Tests for frontend
│  │  ├─ netlify.toml                  # Settings for frontend previews (Netlify)
│  │  ├─ package.json                  # Dependencies for frontend
│  │  ├─ playwright.config.ts          # Settings for frontend tests
│  │  ├─ tsconfig.json                 # Settings for frontend compilation
├─ .pkgr.yml                           # Build definition for Debian/Ubuntu packages
├─ .pre-commit-config.yaml             # Code formatter/linter configuration
├─ CONTRIBUTING.md                     # Contirbution guidelines and overview
├─ Procfile                            # Process definition for Debian/Ubuntu packages
├─ README.md                           # General project information and overview
├─ runtime.txt                         # Python runtime settings for Debian/Ubuntu packages build
├─ SECURITY.md                         # Project security policy
├─ tasks.py                            # Action definitions for development, testing and deployment
```

Refer to our [contribution guidelines](https://docs.inventree.org/en/latest/develop/contributing/) for more information!
