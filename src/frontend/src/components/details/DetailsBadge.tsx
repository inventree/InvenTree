import { Badge } from '@mantine/core';

export type DetailsBadgeProps = {
  color: string;
  label: string;
  size?: string;
  visible?: boolean;
  key?: any;
};

export default function DetailsBadge(props: DetailsBadgeProps) {
  if (props.visible == false) {
    return null;
  }

  return (
    <Badge
      key={props.key}
      color={props.color}
      variant="filled"
      size={props.size ?? 'lg'}
    >
      {props.label}
    </Badge>
  );
}
