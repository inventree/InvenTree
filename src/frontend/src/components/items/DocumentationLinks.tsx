import { Anchor, Group, SimpleGrid, Text } from '@mantine/core';

import { DocTooltip } from './DocTooltip';
import { PlaceholderPill } from './Placeholder';

interface DocumentationLinkBase {
  id: string;
  title: string | JSX.Element;
  description: string | JSX.Element;
  placeholder?: boolean;
}

interface DocumentationLinkItemLink extends DocumentationLinkBase {
  link: string;
  action?: never;
}

interface DocumentationLinkItemAction extends DocumentationLinkBase {
  link?: never;
  action: () => void;
}

export type DocumentationLinkItem =
  | DocumentationLinkItemLink
  | DocumentationLinkItemAction;

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
