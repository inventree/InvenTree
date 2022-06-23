{% load js_i18n %}

/* globals
*/

/* exported
    clearEvents,
    endDate,
    startDate,
    renderDate,
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


/*
 * Render the provided date in the user-specified format.
 *
 * The provided "date" variable is a string, nominally ISO format e.g. 2022-02-22
 * The user-configured setting DATE_DISPLAY_FORMAT determines how the date should be displayed.
 */

function renderDate(date, options={}) {

    if (!date) {
        return null;
    }

    var fmt = user_settings.DATE_DISPLAY_FORMAT || 'YYYY-MM-DD';

    if (options.showTime) {
        fmt += ' HH:mm';
    }

    var m = moment(date);

    if (m.isValid()) {
        return m.format(fmt);
    } else {
        // Invalid input string, simply return provided value
        return date;
    }
}
