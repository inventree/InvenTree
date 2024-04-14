import { Trans } from '@lingui/macro';
import { Carousel } from '@mantine/carousel';
import { Anchor, Button, Paper, Text, Title, rem } from '@mantine/core';

import { DocumentationLinkItem } from './DocumentationLinks';
import * as classes from './GettingStartedCarousel.css';
import { PlaceholderPill } from './Placeholder';

function StartedCard({
  title,
  description,
  link,
  placeholder
}: DocumentationLinkItem) {
  return (
    <Paper shadow="md" p="xl" radius="md" className={classes.card}>
      <div>
        <Title order={3} className={classes.title}>
          {title} {placeholder && <PlaceholderPill />}
        </Title>
        <Text size="sm" className={classes.category} lineClamp={2}>
          {description}
        </Text>
      </div>
      <Anchor href={link} target="_blank">
        <Button>
          <Trans>Read more</Trans>
        </Button>
      </Anchor>
    </Paper>
  );
}

export function GettingStartedCarousel({
  items
}: {
  items: DocumentationLinkItem[];
}) {
  const slides = items.map((item) => (
    <Carousel.Slide key={item.id}>
      <StartedCard {...item} />
    </Carousel.Slide>
  ));

  return (
    <Carousel
      slideSize="50%"
      breakpoints={[{ maxWidth: 'sm', slideSize: '100%', slideGap: rem(2) }]}
      slideGap="xl"
      align="start"
    >
      {slides}
    </Carousel>
  );
}
