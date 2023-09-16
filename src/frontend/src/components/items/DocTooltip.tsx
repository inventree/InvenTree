import { Trans } from '@lingui/macro';
import { Anchor, Container, HoverCard, ScrollArea, Text } from '@mantine/core';
import { useEffect, useRef, useState } from 'react';

import { InvenTreeStyle } from '../../globalStyle';

export interface BaseDocProps {
  text: string | JSX.Element;
  detail?: string | JSX.Element;
  link?: string;
  docchildren?: React.ReactNode;
}

export interface DocTooltipProps extends BaseDocProps {
  children: React.ReactNode;
}

export function DocTooltip({
  children,
  text,
  detail,
  link,
  docchildren
}: DocTooltipProps) {
  const { classes } = InvenTreeStyle();

  return (
    <HoverCard
      shadow="md"
      openDelay={200}
      closeDelay={200}
      withinPortal={true}
      classNames={{ dropdown: classes.docHover }}
    >
      <HoverCard.Target>
        <div>{children}</div>
      </HoverCard.Target>
      <HoverCard.Dropdown>
        <ConstBody
          text={text}
          detail={detail}
          docchildren={docchildren}
          link={link}
        />
      </HoverCard.Dropdown>
    </HoverCard>
  );
}

function ConstBody({
  text,
  detail,
  docchildren,
  link
}: {
  text: string | JSX.Element;
  detail?: string | JSX.Element;
  docchildren?: React.ReactNode;
  link?: string;
}) {
  const [height, setHeight] = useState(0);
  const ref = useRef(null);

  // dynamically set height of scroll area based on content to remove unnecessary scroll bar
  useEffect(() => {
    if (ref.current == null) return;

    let height = ref.current['clientHeight'];
    if (height > 250) {
      setHeight(250);
    } else {
      setHeight(height + 1);
    }
  });

  return (
    <Container maw={400} p={0}>
      <Text>{text}</Text>
      {(detail || docchildren) && (
        <ScrollArea h={height} mah={250}>
          <div ref={ref}>
            {detail && (
              <Text size="xs" color="dimmed">
                {detail}
              </Text>
            )}
            {docchildren}
          </div>
        </ScrollArea>
      )}
      {link && (
        <Anchor href={link} target="_blank">
          <Text size={'sm'}>
            <Trans>Read More</Trans>
          </Text>
        </Anchor>
      )}
    </Container>
  );
}
