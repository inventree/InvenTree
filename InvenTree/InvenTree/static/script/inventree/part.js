/* Part API functions
 * Requires api.js to be loaded first
 */

function toggleStar(options) {
    /* Toggle the 'starred' status of a part.
     * Performs AJAX queries and updates the display on the button.
     * 
     * options:
     * - button: ID of the button (default = '#part-star-icon')
     * - part: pk of the part object
     * - user: pk of the user
     */

    var url = '/api/part/star/';

    inventreeGet(
        url,
        {
            part: options.part,
            user: options.user,
        },
        {
            success: function(response) {
                if (response.length == 0) {
                    // Zero length response = star does not exist
                    // So let's add one!
                    inventreePut(
                        url,
                        {
                            part: options.part,
                            user: options.user,
                        },
                        {
                            method: 'POST',
                            success: function(response, status) {
                                $(options.button).addClass('icon-yellow');
                            },
                        }
                    );
                } else {
                    var pk = response[0].pk;
                    // There IS a star (delete it!)
                    inventreePut(
                        url + pk + "/",
                        {
                        },
                        {
                            method: 'DELETE',
                            success: function(response, status) {
                                $(options.button).removeClass('icon-yellow');
                            },
                        }
                    );
                }
            },
        }
    );
}