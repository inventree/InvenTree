## InvenTree Roadmap

### Design Goals

InvenTree is intened to provide a stand-alone stock-management system that runs completely offline.

It is designed to be run on a local server, and should not require the use of plugins/scripts that phone-home or load external content.

(This ignores the use of bespoke plugins that may be implemented down the line, e.g. for OctoPart integration, etc)

### 0.1 Release

The goals for the initial release should be limited to the following:

1. Fully implement a JSON API for the various apps and models
1. Design an initial front-end for querying data using this API
   * Single-pase design is preferred, for the sake of responsiveness and intuitive interaction
   * Investigate JS/AJAX engine - Angular? Bootstrap?
1. Allow users to view part category tree 
1. Allow users to view all parts in a given category
1. "" edit parts
1. "" add new parts

### TODO

Research needed!

django-restful in combination with angular seems the way to go. Extra tools provided via https://github.com/jrief/django-angular
