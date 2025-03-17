// Helper function to cancel event propagation
export function cancelEvent(event: any) {
  event?.preventDefault();
  event?.stopPropagation();
  event?.nativeEvent?.stopImmediatePropagation();
}
