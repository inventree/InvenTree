## Error Codes

InvenTree is starting to use error codes to help identify and diagnose issues. These are increasingly being added to the codebase. Error messages missing an error code should be reported on GitHub.
Error codes are prefixed with `INVE-` and are followed by a letter to indicate the type of error and a number to indicate the specific error. Once a code is used it might not be reassigned to a different error, it can be marked as stricken from the list.

### INVE-E (InvenTree Error)
Errors - These are critical errors which should be addressed as soon as possible.

#### INVE-E1
**No frontend included - Backend/web**

Only stable / production releases of InvenTree include the frontend panel. This is both a measure of resource-saving and attack surface reduction. If you want to use the frontend panel, you can either:″
- use a docker image that is version-tagged or the stable version
- use a package version that is from the stable or version stream
- install node and yarn on the server to build the frontend with the [invoke](../start/invoke.md) task `int.frontend-build`

Raise an issue if none of these options work.

#### INVE-E2
**Wrong Invoke Path**

The used invoke executable is the wrong one. InvenTree needs to have
You probably have a reference to invoke or a directory with invoke in your PATH variable that is not in InvenTrees virtual environment. You can check this by running `which invoke` and `which python` in your installations base directory and compare the output. If they are not the same, you need to adjust your PATH variable to point to the correct virtual environment before it lists other directories with invoke.

### INVE-W (InvenTree Warning)
Warnings - These are non-critical errors which should be addressed when possible.

#### INVE-W1
**Current branch could not be detected - Backend**

During startup of the backend InvenTree tries to detect branch, commit hash and commit date to surface on various points in the UI, through tags and in the API.
This information is not needed for operation but very helpful for debugging and support. These issues might be caused by running a deployment version that delivers without git information, not having git installed or not having dulwich installed.
You can ignore this warning if you are not interested in the git information.

#### INVE-W2
**Dulwich module not found - Backend**

See [INVE-W1](#inve-w1)

#### INVE-W3
**Could not detect git information - Backend**

See [INVE-W1](#inve-w1)


### INVE-I (InvenTree Information)
Information — These are not errors but information messages. They might point out potential issues or just provide information.

### INVE-M (InvenTree Miscellaneous)
Miscellaneous — These are information messages that might be used to mark debug information or other messages helpful for the InvenTree team to understand behaviour.
