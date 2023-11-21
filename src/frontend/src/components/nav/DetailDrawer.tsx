import { Drawer, Text } from '@mantine/core';
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
}

function DetailDrawerComponent({
  title,
  position = 'right',
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
      title={
        <Text size="xl" fw={600} variant="gradient">
          {title}
        </Text>
      }
      overlayProps={{ opacity: 0.5, blur: 4 }}
    >
      {content}
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
