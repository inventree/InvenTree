/**
 * A sample action plugin for InvenTree.
 *
 * This is a very basic example of how to define a custom action.
 * In practice, you would want to implement more complex logic here.
 */

export function performSampleAction(data) {
    // Simply log the data to the console
    alert("Sample! Refer to the console");
    console.log("Sample action performed with data:", data);
}
