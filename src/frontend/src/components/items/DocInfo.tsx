import { IconInfoCircle } from '@tabler/icons-react';

import { type BaseDocProps, DocTooltip } from './DocTooltip';

interface DocInfoProps extends BaseDocProps {
  size?: number;
}

export function DocInfo({
  size = 18,
  text,
  detail,
  link
}: Readonly<DocInfoProps>) {
  return (
    <DocTooltip text={text} detail={detail} link={link}>
      <IconInfoCircle size={size} />
    </DocTooltip>
  );
}
