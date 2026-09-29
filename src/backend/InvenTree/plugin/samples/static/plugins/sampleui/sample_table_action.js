/** A sample table action; the selection is captured when the button is clicked. */
export function getFeature({ featureContext }) {
  const { selectedIds } = featureContext;
  alert(`Selected stock item IDs: ${selectedIds.join(', ')}`);
}
