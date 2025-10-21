import { Badge } from '@mantine/core';

export type DetailsBadgeProps = {
  color: string;
  label: string;
  size?: string;
  visible?: boolean;
};

export default function DetailsBadge(props: Readonly<DetailsBadgeProps>) {
  if (props.visible == false) {
    return null;
  }

  return (
    <Badge color={props.color} variant='filled' size={props.size ?? 'lg'}>
      {props.label}
    </Badge>
  );
}
