import { Badge, Tooltip } from '@mantine/core';

export type DetailsBadgeProps = {
  color: string;
  label: string;
  size?: string;
  visible?: boolean;
  tooltip?: string;
};

export default function DetailsBadge(props: Readonly<DetailsBadgeProps>) {
  if (props.visible == false) {
    return null;
  }

  return (
    <Tooltip
      label={props.tooltip}
      disabled={!props.tooltip}
      position='bottom'
      withArrow
    >
      <Badge color={props.color} variant='filled' size={props.size ?? 'lg'}>
        {props.label}
      </Badge>
    </Tooltip>
  );
}
