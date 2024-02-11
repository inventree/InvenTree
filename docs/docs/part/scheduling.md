---
title: Part Scheduling
---

## Part Scheduling


The *Scheduling* tab provides an overview of the *predicted* future availabile quantity of a particular part.

The *Scheduling* tab displays a chart of estimated future part stock levels. It begins at the current date, with the current stock level. It then projects into the "future", taking information from:

#### Incoming Stock

- **Purchase Orders** - Incoming goods will increase stock levels
- **Build Orders** - Completed build outputs will increase stock levels

#### Outgoing Stock

- **Sales Orders** - Outgoing stock items will reduce stock levels
- **Build Orders** - Allocated stock items will reduce stock levels

#### Caveats

The scheduling information only works as an adequate predictor of future stock quantity if there is sufficient information available in the database.

In particular, stock movements due to orders (Purchase Orders / Sales Orders / Build Orders) will only be counted in the scheduling *if a target date is set for the order*. If the order does not have a target date set, we cannot know *when* (in the future) the stock levels will be adjusted. Thus, orders without target date information do not contribute to the scheduling information.

Additionally, any orders with a target date in the "past" are also ignored for the purpose of part scheduling.

Finally, any unexpected or unscheduled stock operations which are not associated with future orders cannot be predicted or displayed in the scheduling tab.

{% with id="scheduling", url="part/scheduling.png", description="Part Scheduling View" %}
{% include 'img.html' %}
{% endwith %}
