import { InvenTreeLogo } from '../items/InvenTreeLogo';
import { Container, Group, Anchor } from '@mantine/core';
import { InvenTreeStyle } from '../../globalStyle';
import { links } from '../../defaults';

export function Footer() {
  const { classes } = InvenTreeStyle();
  const items = links.map((link) => (
    <Anchor<'a'>
      color="dimmed"
      key={link.label}
      href={link.link}
      onClick={(event) => event.preventDefault()}
      size="sm"
    >
      {link.label}
    </Anchor>
  ));

  return (
    <div className={classes.footer}>
      <Container className={classes.inner}>
        <InvenTreeLogo />
        <Group className={classes.links}>{items}</Group>
      </Container>
    </div>
  );
}
