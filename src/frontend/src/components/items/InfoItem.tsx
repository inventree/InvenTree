import { Trans } from '@lingui/macro';
import { Code, Flex, Group, Text } from '@mantine/core';
import { Link, type To } from 'react-router-dom';

import { YesNoButton } from '../buttons/YesNoButton';
import { DetailDrawerLink } from '../nav/DetailDrawer';

export function InfoItem({
  name,
  children,
  type,
  value,
  link,
  detailDrawerLink
}: Readonly<{
  name: string;
  children?: React.ReactNode;
  type?: 'text' | 'boolean' | 'code';
  value?: any;
  link?: To;
  detailDrawerLink?: boolean;
}>) {
  function renderComponent() {
    if (value === undefined) return null;

    if (type === 'text') {
      return <Text>{value || <Trans>None</Trans>}</Text>;
    }

    if (type === 'boolean') {
      return <YesNoButton value={value || false} />;
    }

    if (type === 'code') {
      return (
        <Code style={{ wordWrap: 'break-word', maxWidth: '400px' }}>
          {value}
        </Code>
      );
    }

    return null;
  }

  return (
    <Group justify='space-between'>
      <Text fz='sm' fw={700}>
        {name}:
      </Text>
      <Flex>
        {children}
        {link ? (
          detailDrawerLink ? (
            <DetailDrawerLink to={link} text={value} />
          ) : (
            <Link to={link}>{renderComponent()}</Link>
          )
        ) : (
          renderComponent()
        )}
      </Flex>
    </Group>
  );
}
