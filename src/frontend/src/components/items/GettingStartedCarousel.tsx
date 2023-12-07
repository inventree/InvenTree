import { Trans } from '@lingui/macro';
import { Carousel } from '@mantine/carousel';
import {
  Anchor,
  Button,
  Paper,
  Text,
  Title,
  createStyles,
  rem
} from '@mantine/core';

import { DocumentationLinkItem } from './DocumentationLinks';
import { PlaceholderPill } from './Placeholder';

const useStyles = createStyles((theme) => ({
  card: {
    height: rem(170),
    display: 'flex',
    flexDirection: 'column',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    backgroundSize: 'cover',
    backgroundPosition: 'center'
  },

  title: {
    fontWeight: 900,
    color:
      theme.colorScheme === 'dark' ? theme.colors.white : theme.colors.dark,
    lineHeight: 1.2,
    fontSize: rem(32),
    marginTop: 0
  },

  category: {
    color:
      theme.colorScheme === 'dark' ? theme.colors.white : theme.colors.dark,
    opacity: 0.7,
    fontWeight: 700
  }
}));

function StartedCard({
  title,
  description,
  link,
  placeholder
}: DocumentationLinkItem) {
  const { classes } = useStyles();

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
