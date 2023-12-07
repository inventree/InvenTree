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
  const DocumentationLinkRenderer = ({
    link
  }: {
    link: DocumentationLinkItem;
  }) => {
    const content = (
      <Text size="sm" fw={500}>
        {link.title}
      </Text>
    );

    const Linker = ({ children }: { children: any }) => {
      if (link.link)
        return (
          <Anchor href={link.link} key={link.id}>
            {children}
          </Anchor>
        );

      if (link.action)
        return (
          <Anchor component="button" type="button" onClick={link.action}>
            {children}
          </Anchor>
        );

      console.log('Neither link nor action found for link:', link);
      return children;
    };

    return (
      <Linker>
        {link.placeholder ? (
          <Group>
            {content}
            <PlaceholderPill />
          </Group>
        ) : (
          content
        )}
      </Linker>
    );
  };

  return (
    <SimpleGrid cols={2} spacing={0}>
      {links.map((link) => (
        <DocTooltip key={link.id} text={link.description}>
          <DocumentationLinkRenderer link={link} />
        </DocTooltip>
      ))}
    </SimpleGrid>
  );
}
