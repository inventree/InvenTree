import { Anchor, SimpleGrid, Text } from '@mantine/core';

import { DocTooltip } from './DocTooltip';

export interface DocumentationLinkItem {
  title: string;
  description: string;
  link: string;
}

export function DocumentationLinks({
  links
}: {
  links: DocumentationLinkItem[];
}) {
  return (
    <SimpleGrid cols={2} spacing={0}>
      {links.map((link) => (
        <DocTooltip key={link.title} text={link.description}>
          <Anchor href={link.link} key={link.title}>
            <Text size="sm" fw={500}>
              {link.title}
            </Text>
          </Anchor>
        </DocTooltip>
      ))}
    </SimpleGrid>
  );
}
