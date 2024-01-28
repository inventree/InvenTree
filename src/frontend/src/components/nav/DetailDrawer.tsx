import {
  ActionIcon,
  Divider,
  Drawer,
  Group,
  MantineNumberSize,
  Stack,
  Text
} from '@mantine/core';
import { IconChevronLeft } from '@tabler/icons-react';
import { useMemo } from 'react';
import { Route, Routes, useNavigate, useParams } from 'react-router-dom';

/**
 * @param title - drawer title
 * @param position - drawer position
 * @param renderContent - function used to render the drawer content
 * @param urlPrefix - set an additional url segment, useful when multiple drawers are rendered on one page (e.g. "user/")
 */
export interface DrawerProps {
  title: string;
  position?: 'right' | 'left';
  renderContent: (id?: string) => React.ReactNode;
  urlPrefix?: string;
  size?: MantineNumberSize;
}

function DetailDrawerComponent({
  title,
  position = 'right',
  size,
  renderContent
}: DrawerProps) {
  const navigate = useNavigate();
  const { id } = useParams();

  const content = renderContent(id);
  const opened = useMemo(() => !!id && !!content, [id, content]);

  return (
    <Drawer
      opened={opened}
      onClose={() => navigate('../')}
      position={position}
      size={size}
      title={
        <Group>
          <ActionIcon variant="outline" onClick={() => navigate(-1)}>
            <IconChevronLeft />
          </ActionIcon>
          <Text size="xl" fw={600} variant="gradient">
            {title}
          </Text>
        </Group>
      }
    >
      <Stack spacing={'xs'}>
        <Divider />
        {content}
      </Stack>
    </Drawer>
  );
}

export function DetailDrawer(props: DrawerProps) {
  return (
    <Routes>
      <Route path=":id?/" element={<DetailDrawerComponent {...props} />} />
    </Routes>
  );
}
