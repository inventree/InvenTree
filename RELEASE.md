## Release Checklist

Checklist of steps to perform at each code release

### Update Version String

Update `INVENTREE_SW_VERSION` in [version.py](https://github.com/inventree/InvenTree/blob/master/InvenTree/InvenTree/version.py)

### Increment API Version

If the API has changed, ensure that the API version number is incremented.

### Translation Files

Merge the crowdin translation updates into master branch

### Python Library Release

Create new release for the [InvenTree python library](https://github.com/inventree/inventree-python)

## App Release

Create new versioned release for the InvenTree mobile app.
