{% load i18n %}

/* globals
*/

/* exported
    clearEvents,
    endDate,
    startDate,
*/

/**
 * Helper functions for calendar display
 */

function startDate(calendar) {
    // Extract the first displayed date on the calendar
    return calendar.currentData.dateProfile.activeRange.start.toISOString().split('T')[0];
}

function endDate(calendar) {
    // Extract the last display date on the calendar
    return calendar.currentData.dateProfile.activeRange.end.toISOString().split('T')[0];
}

function clearEvents(calendar) {
    // Remove all events from the calendar

    var events = calendar.getEvents();

    events.forEach(function(event) {
        event.remove();
    });
}
