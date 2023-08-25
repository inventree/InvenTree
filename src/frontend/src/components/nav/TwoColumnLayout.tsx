import { Grid, Group } from '@mantine/core';
import React from 'react';

import { PlaceholderPill } from '../items/Placeholder';
import { StylishText } from '../items/StylishText';

export function TwoColumnLayout({
  title,
  children,
  sidebar,
  is_placeholder = false
}: {
  title: string | JSX.Element;
  children: React.ReactNode;
  sidebar: React.ReactNode;
  is_placeholder: boolean;
}) {
  return (
    <>
      <Group>
        <StylishText>{title}</StylishText>
        {is_placeholder && <PlaceholderPill />}
      </Group>
      <Grid grow>
        <Grid.Col span={8} sx={{ overflow: 'auto' }}>
          {children}
        </Grid.Col>
        <Grid.Col span={2} sx={{ overflow: 'auto' }}>
          {sidebar}
        </Grid.Col>
      </Grid>
    </>
  );
}
