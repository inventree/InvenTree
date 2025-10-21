import type { ReactNode } from 'react';

/**
 * A component that expands to fill the available space
 */
export default function Expand({
  children,
  flex
}: {
  children: ReactNode;
  flex?: number;
}) {
  return <div style={{ flexGrow: flex ?? 1 }}>{children}</div>;
}
