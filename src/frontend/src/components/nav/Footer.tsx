import { Anchor, Container, Group } from '@mantine/core';

import { footerLinks } from '../../defaults/links';
import { InvenTreeStyle } from '../../globalStyle';
import { InvenTreeLogoHomeButton } from '../items/InvenTreeLogo';

export function Footer() {
  const { classes } = InvenTreeStyle();
  const items = footerLinks.map((link) => (
    <Anchor<'a'>
      color="dimmed"
      key={link.key}
      href={link.link}
      onClick={(event) => event.preventDefault()}
      size="sm"
    >
      {link.label}
    </Anchor>
  ));

  return (
    <div className={classes.layoutFooter}>
      <Container className={classes.layoutFooterInner} size={'100%'}>
        <InvenTreeLogoHomeButton />
        <Group className={classes.layoutFooterLinks}>{items}</Group>
      </Container>
    </div>
  );
}
