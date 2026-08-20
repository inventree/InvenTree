import { Group } from '@mantine/core';
import { useState } from 'react';
import { CopyButton } from '../components/buttons/CopyButton';

/**
 * A wrapper component that adds a copy button to cell content on hover
 * This component is used to make table cells copyable without adding visual clutter
 *
 * @param children - The cell content to render
 * @param value - The value to copy when the copy button is clicked
 */
export function CopyableCell({
  children,
  value
}: Readonly<{
  children: React.ReactNode;
  value: string;
}>) {
  const [isHovered, setIsHovered] = useState(false);

  return (
    <Group
      gap={0}
      p={0}
      wrap='nowrap'
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      justify='space-between'
      align='center'
    >
      {children}
      {window.isSecureContext && isHovered && value != null && (
        <span
          style={{ position: 'relative' }}
          onClick={(e) => e.stopPropagation()}
          onKeyDown={(e) => e.stopPropagation()}
        >
          <div
            style={{
              position: 'absolute',
              right: 0,
              transform: 'translateY(-50%)'
            }}
          >
            <CopyButton value={value} variant={'default'} />
          </div>
        </span>
      )}
    </Group>
  );
}
