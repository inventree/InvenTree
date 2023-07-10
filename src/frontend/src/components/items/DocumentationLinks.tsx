import { Anchor, SimpleGrid, Text } from '@mantine/core';

import { DocTooltip } from './DocTooltip';

export interface DocumentationLinkItem {
  id: string;
  title: string | JSX.Element;
  description: string | JSX.Element;
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
        <DocTooltip key={link.id} text={link.description}>
          <Anchor href={link.link} key={link.id}>
            <Text size="sm" fw={500}>
              {link.title}
            </Text>
          </Anchor>
        </DocTooltip>
      ))}
    </SimpleGrid>
  );
}
