import { Trans } from '@lingui/macro';
import { Carousel } from '@mantine/carousel';
import { Anchor, Button, Paper, Text } from '@mantine/core';

import * as classes from './GettingStartedCarousel.css';
import type { MenuLinkItem } from './MenuLinks';
import { StylishText } from './StylishText';

function StartedCard({ title, description, link }: Readonly<MenuLinkItem>) {
  return (
    <Paper shadow='md' p='xl' radius='md' className={classes.card}>
      <div>
        <StylishText size='md'>{title}</StylishText>
        <Text size='sm' className={classes.category} lineClamp={2}>
          {description}
        </Text>
      </div>
      <Anchor href={link} target='_blank'>
        <Button>
          <Trans>Read More</Trans>
        </Button>
      </Anchor>
    </Paper>
  );
}

export function GettingStartedCarousel({
  items
}: Readonly<{
  items: MenuLinkItem[];
}>) {
  const slides = items.map((item) => (
    <Carousel.Slide key={item.id}>
      <StartedCard {...item} />
    </Carousel.Slide>
  ));

  return (
    <Carousel
      slideSize={{ base: '100%', sm: '50%', md: '33.333333%' }}
      slideGap={{ base: 0, sm: 'md' }}
      slidesToScroll={3}
      align='start'
      loop
    >
      {slides}
    </Carousel>
  );
}
