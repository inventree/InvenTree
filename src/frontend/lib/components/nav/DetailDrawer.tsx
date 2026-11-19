import { ActionIcon, Divider, Drawer, Group, Stack, Text } from '@mantine/core';
import { IconChevronLeft } from '@tabler/icons-react';
import { useCallback, useMemo } from 'react';
import { Link, Route, Routes, useNavigate, useParams } from 'react-router-dom';
import type { To } from 'react-router-dom';

import type { UiSizeType } from '../../types/Core';

import { useShallow } from 'zustand/react/shallow';
import { useLocalLibState } from '../../states/LocalLibState';
import { StylishText } from '../StylishText';
import * as classes from './DetailDrawer.css';

/**
 * @param title - drawer title
 * @param position - drawer position
 * @param renderContent - function used to render the drawer content
 * @param urlPrefix - set an additional url segment, useful when multiple drawers are rendered on one page (e.g. "user/")
 * @param onBeforeClose - optional callback to intercept closing of the drawer (e.g. to confirm unsaved changes). Call the provided "close" function to actually close the drawer.
 */
export interface DrawerProps {
  title: string;
  position?: 'right' | 'left';
  renderContent: (id?: string) => React.ReactNode;
  urlPrefix?: string;
  size?: UiSizeType;
  closeOnEscape?: boolean;
  onBeforeClose?: (close: () => void) => void;
}

export function DetailDrawerComponent({
  title,
  position = 'right',
  size,
  closeOnEscape = true,
  renderContent,
  onBeforeClose
}: Readonly<DrawerProps>) {
  const navigate = useNavigate();
  const { id } = useParams();

  const content = renderContent(id);
  const opened = useMemo(() => !!id && !!content, [id, content]);

  const [detailDrawerStack, addDetailDrawer] = useLocalLibState(
    useShallow((state) => [state.detailDrawerStack, state.addDetailDrawer])
  );

  // Run a "close" action, optionally allowing the owner of the drawer to intercept it
  const guardedClose = useCallback(
    (close: () => void) => {
      if (onBeforeClose) {
        onBeforeClose(close);
      } else {
        close();
      }
    },
    [onBeforeClose]
  );

  return (
    <Drawer
      opened={opened}
      onClose={() =>
        guardedClose(() => {
          navigate('../');
          addDetailDrawer(false);
        })
      }
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
              onClick={() =>
                guardedClose(() => {
                  navigate(-1);
                  addDetailDrawer(-1);
                })
              }
            >
              <IconChevronLeft />
            </ActionIcon>
          )}
          <StylishText size='xl'>{title}</StylishText>
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
  const addDetailDrawer = useLocalLibState(
    useShallow((state) => state.addDetailDrawer)
  );

  const onNavigate = useCallback(() => {
    addDetailDrawer(1);
  }, [addDetailDrawer]);

  return (
    <Link to={to} onClick={onNavigate}>
      <Text>{text}</Text>
    </Link>
  );
}
