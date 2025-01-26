## Error Codes

InvenTree is starting to use error codes to help identify and diagnose issues. These are increasengly being added to the codebase. Error messages missing an error code should be reported on GitHub.
Error codes are prefixed with `INVE-` and are followed by a letter to indicate the type of error and a number to indicate the specific error. Once a code was used it might not be reasigned to a different error, it can be marked as stricken from the list.

### INVE-E (InvenTree Error)
Errors - These are critical errors which should be addressed as soon as possible.

#### INVE-E1
**No frontend included - Backend/web**

Only stable / production releases of InvenTree include the frontend panel. This is both a measure of resource saving and attack surfcace reduction. If you want to use the frontend panel, you can either:″
- use a docker image that is version tagged or the stable version
- use a package version that is from the stable or version stream
- install node and yarn on the server to build the frontend with the [invoke](../start/invoke.md) task `int.frontend-build`

Raise an issue if none of these options work.

### INVE-W (InvenTree Warning)
Warnings - These are non-critical errors which should be addressed when possible.

### INVE-I (InvenTree Information)
Information - These are not errors but information messages. These might point out potential issues or just provide information.

### INVE-M (InvenTree Miscealaneous)
Miscellaneous - These are information messages that might be used for marking debug information or other messages helpful for the InvenTree team to understand behaviour.
