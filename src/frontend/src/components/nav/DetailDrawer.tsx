import { ActionIcon, Divider, Drawer, Group, Stack, Text } from '@mantine/core';
import { IconChevronLeft } from '@tabler/icons-react';
import { useCallback, useMemo } from 'react';
import { Link, Route, Routes, useNavigate, useParams } from 'react-router-dom';
import type { To } from 'react-router-dom';

import type { UiSizeType } from '../../defaults/formatters';
import { useLocalState } from '../../states/LocalState';
import * as classes from './DetailDrawer.css';

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
  size?: UiSizeType;
  closeOnEscape?: boolean;
}

function DetailDrawerComponent({
  title,
  position = 'right',
  size,
  closeOnEscape = true,
  renderContent
}: Readonly<DrawerProps>) {
  const navigate = useNavigate();
  const { id } = useParams();

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
      closeOnEscape={closeOnEscape}
      size={size}
      classNames={{ root: classes.flex, body: classes.flex }}
      scrollAreaComponent={Stack}
      title={
        <Group>
          {detailDrawerStack > 0 && (
            <ActionIcon
              variant='outline'
              onClick={() => {
                navigate(-1);
                addDetailDrawer(-1);
              }}
            >
              <IconChevronLeft />
            </ActionIcon>
          )}
          <Text size='xl' fw={600} variant='gradient'>
            {title}
          </Text>
        </Group>
      }
    >
      <Stack gap={'xs'} className={classes.flex}>
        <Divider />
        {content}
      </Stack>
    </Drawer>
  );
}

export function DetailDrawer(props: Readonly<DrawerProps>) {
  return (
    <Routes>
      <Route path=':id?/' element={<DetailDrawerComponent {...props} />} />
    </Routes>
  );
}

export function DetailDrawerLink({
  to,
  text
}: Readonly<{ to: To; text: string }>) {
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
