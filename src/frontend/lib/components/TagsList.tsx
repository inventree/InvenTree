import { ActionIcon, Badge, Group, Paper } from '@mantine/core';
import { IconTag } from '@tabler/icons-react';

export default function TagsList({
  tags
}: Readonly<{
  tags: string[];
}>) {
  if (!tags || tags.length === 0) {
    return null;
  }

  return (
    <Paper p='xs' shadow='xs' withBorder>
      <Group gap='xs'>
        <ActionIcon size='sm' variant='transparent'>
          <IconTag />
        </ActionIcon>
        {tags.map((tag: string) => (
          <Badge key={tag} variant='outline' size='sm'>
            {tag}
          </Badge>
        ))}
      </Group>
    </Paper>
  );
}
