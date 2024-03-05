import {
  ActionIcon,
  Divider,
  Drawer,
  Group,
  MantineNumberSize,
  Stack,
  Text,
  createStyles
} from '@mantine/core';
import { IconChevronLeft } from '@tabler/icons-react';
import { useCallback, useMemo } from 'react';
import { Link, Route, Routes, useNavigate, useParams } from 'react-router-dom';
import type { To } from 'react-router-dom';

import { useLocalState } from '../../states/LocalState';

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

const useStyles = createStyles(() => ({
  flex: {
    display: 'flex',
    flex: 1
  }
}));

function DetailDrawerComponent({
  title,
  position = 'right',
  size,
  renderContent
}: DrawerProps) {
  const navigate = useNavigate();
  const { id } = useParams();
  const { classes } = useStyles();

  const content = renderContent(id);
  const opened = useMemo(() => !!id && !!content, [id, content]);

  const [detailDrawerStack, addDetailDrawer] = useLocalState((state) => [
    state.detailDrawerStack,
    state.addDetailDrawer
  ]);

  return (
    <Drawer
      opened={opened}
      onClose={() => {
        navigate('../');
        addDetailDrawer(false);
      }}
      position={position}
      size={size}
      classNames={{ root: classes.flex, body: classes.flex }}
      scrollAreaComponent={Stack}
      title={
        <Group>
          {detailDrawerStack > 0 && (
            <ActionIcon
              variant="outline"
              onClick={() => {
                navigate(-1);
                addDetailDrawer(-1);
              }}
            >
              <IconChevronLeft />
            </ActionIcon>
          )}
          <Text size="xl" fw={600} variant="gradient">
            {title}
          </Text>
        </Group>
      }
    >
      <Stack spacing={'xs'} className={classes.flex}>
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

export function DetailDrawerLink({ to, text }: { to: To; text: string }) {
  const addDetailDrawer = useLocalState((state) => state.addDetailDrawer);

  const onNavigate = useCallback(() => {
    addDetailDrawer(1);
  }, [addDetailDrawer]);

  return (
    <Link to={to} onClick={onNavigate}>
      <Text>{text}</Text>
    </Link>
  );
}
