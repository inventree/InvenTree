---
title: Data Download
---

## Data Download

Some API endpoints provide a *download* function, whereby the data presented at the API endpoint can be downloaded as a tabulated file.

To export API data to a file, add the `&export=<format>` modifier to the query. The following file formats are supported:

| File Format | Modifier |
| --- | --- |
| csv | `&format=csv` |
| tsv | `&format=tsv` |
| xls | `&format=xls` |
| xlsx | `&format=xlsx` |

### Query Filters

Any other query filters used in the API request are also observed when downloading the data. For example, to download a list of all stock items in a given location:

`<host>/api/stock/?format=csv&location=10`
