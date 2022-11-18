import { InvenTreeLogo } from "../InvenTreeLogo";
import { Container, Group, Anchor } from '@mantine/core';
import { useStyles } from "../../globalStyle";


export interface FooterSimpleProps { links: { link: string; label: string }[] }

export function FooterSimple({ links }: FooterSimpleProps) {
  const { classes } = useStyles();
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
