import { Anchor, Group, SimpleGrid, Text } from '@mantine/core';

import { DocTooltip } from './DocTooltip';
import { PlaceholderPill } from './Placeholder';

interface DocumentationLinkItem {
  id: string;
  title: string | JSX.Element;
  description: string | JSX.Element;
  placeholder?: boolean;
}

interface DocumentationLinkItemLink extends DocumentationLinkItem {
  link: string;
  action?: never;
}

interface DocumentationLinkItemAction extends DocumentationLinkItem {
  link?: never;
  action: () => void;
}

export type DocumentationLinkCollection = (
  | DocumentationLinkItemLink
  | DocumentationLinkItemAction
)[];

export function DocumentationLinks({
  links
}: {
  links: DocumentationLinkCollection;
}) {
  return (
    <SimpleGrid cols={2} spacing={0}>
      {links.map((link) => (
        <DocTooltip key={link.id} text={link.description}>
          <Anchor href={link.link} key={link.id}>
            {link.placeholder ? (
              <Group>
                <Text size="sm" fw={500}>
                  {link.title}
                </Text>
                <PlaceholderPill />
              </Group>
            ) : (
              <Text size="sm" fw={500}>
                {link.title}
              </Text>
            )}
          </Anchor>
        </DocTooltip>
      ))}
    </SimpleGrid>
  );
}
