import { Group, Title, type TitleProps } from '@mantine/core';

import { DocInfo } from './DocInfo';

interface DocTitleProps extends TitleProps {
  text?: string;
  detail?: string;
}

export function TitleWithDoc({
  children,
  variant,
  order,
  size,
  text,
  detail
}: Readonly<DocTitleProps>) {
  return (
    <Group>
      <Title variant={variant} order={order} size={size}>
        {children}
      </Title>
      {text && <DocInfo text={text} detail={detail} />}
    </Group>
  );
}
