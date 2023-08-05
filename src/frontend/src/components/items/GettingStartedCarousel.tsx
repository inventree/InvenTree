import { Carousel } from '@mantine/carousel';
import {
  Button,
  Paper,
  Text,
  Title,
  createStyles,
  rem,
  useMantineTheme
} from '@mantine/core';
import { useMediaQuery } from '@mantine/hooks';

import { gettingStartedList } from '../../defaults/gettingStartedList';

const useStyles = createStyles((theme) => ({
  card: {
    height: rem(200),
    display: 'flex',
    flexDirection: 'column',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    backgroundSize: 'cover',
    backgroundPosition: 'center'
  },

  title: {
    fontFamily: `Greycliff CF, ${theme.fontFamily}`,
    fontWeight: 900,
    color: theme.white,
    lineHeight: 1.2,
    fontSize: rem(32),
    marginTop: theme.spacing.xs
  },

  category: {
    color: theme.white,
    opacity: 0.7,
    fontWeight: 700,
    textTransform: 'uppercase'
  }
}));

function Card({ title, description, link }: DocumentationLinkItem) {
  const { classes } = useStyles();

  return (
    <Paper shadow="md" p="xl" radius="md" className={classes.card}>
      <div>
        <Title order={3} className={classes.title}>
          {title}
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
      <Card {...item} />
    </Carousel.Slide>
  ));

  return (
    <Carousel
      slideSize="50%"
      breakpoints={[{ maxWidth: 'sm', slideSize: '100%', slideGap: rem(2) }]}
      slideGap="xl"
      align="start"
      slidesToScroll={mobile ? 1 : 2}
    >
      {slides}
    </Carousel>
  );
}
