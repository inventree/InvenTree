// Fix for issue #12245: dashboard widgets cannot be dragged or resized
var dashboardWidgets = document.querySelectorAll('.dashboard-widget');
dashboardWidgets.forEach(function(widget) {
  widget.draggable = true;
  widget.resizable = true;
});