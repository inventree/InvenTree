import { Trans, t } from '@lingui/macro';
import {
  ActionIcon,
  Button,
  Divider,
  Drawer,
  Group,
  Indicator,
  List,
  Pill,
  Stack,
  Text,
  TextInput
} from '@mantine/core';
import { useDisclosure } from '@mantine/hooks';
import { IconEyeDotted, IconLink } from '@tabler/icons-react';
import { useEffect, useMemo, useState } from 'react';
import { useLocation } from 'react-router-dom';
import useWebSocket, { ReadyState } from 'react-use-websocket';

import { useLocalState } from '../../states/LocalState';
import { StylishText } from '../items/StylishText';

interface PageMessages {
  type: 'chat_message' | 'users' | 'unknown';
  message: string;
  data: any | null;
  user: string;
}

export const PageAttendanceComponent = () => {
  const [host] = useLocalState((state) => [state.host]);
  const location = useLocation();
  const [socketUrl, setSocketUrl] = useState<string | null>(null);

  // websocket history
  const [messageHistory, setMessageHistory] = useState<MessageEvent<any>[]>([]);
  const [parsedMessageHistory, setParsedMessageHistory] = useState<
    PageMessages[]
  >([]);
  const [
    isAttendanceDrawerOpened,
    { open: openAttendanceDrawer, close: closeAttendanceDrawer }
  ] = useDisclosure(false);

  const messageCount = useMemo(() => {
    return parsedMessageHistory.filter(
      (message) => message.type === 'chat_message'
    ).length;
  }, [parsedMessageHistory]);

  // Websockets
  useEffect(() => {
    setMessageHistory([]);
    setParsedMessageHistory([]);
    let new_room_name = location.pathname.slice(1).replaceAll('/', '__');
    if (new_room_name === '') new_room_name = 'home';
    const cleaned_host = host.replace(/(^\w+:|^)\/\//, '');
    setSocketUrl(`ws://${cleaned_host}/ws/page/${new_room_name}/`);
  }, [host, location.pathname]);
  const { sendMessage, lastMessage, readyState } = useWebSocket(socketUrl);

  useEffect(() => {
    if (lastMessage !== null) {
      setMessageHistory((prev) => prev.concat(lastMessage));
      setParsedMessageHistory((prev) =>
        prev.concat(JSON.parse(lastMessage.data))
      );
    }
  }, [lastMessage]);

  return (
    <Indicator
      radius="lg"
      size="18"
      label={messageCount}
      color="red"
      disabled={messageCount <= 0}
      inline
    >
      <ActionIcon onClick={openAttendanceDrawer} variant="transparent">
        <IconEyeDotted />
      </ActionIcon>
      <AttendanceDrawer
        opened={isAttendanceDrawerOpened}
        onClose={() => {
          closeAttendanceDrawer();
        }}
        sendMessage={sendMessage}
        readyState={readyState}
        messages={parsedMessageHistory}
      />
    </Indicator>
  );
};

function AttendanceDrawer({
  opened,
  onClose,
  sendMessage,
  readyState,
  messages
}: {
  opened: boolean;
  onClose: () => void;
  sendMessage: (message: string) => void;
  readyState: ReadyState;
  messages: PageMessages[];
}) {
  const [inputValue, setInputValue] = useState('');
  function handleClickSendMessage() {
    sendMessage(JSON.stringify({ message: inputValue }));
    setInputValue('');
  }
  const connectionStatus = {
    [ReadyState.CONNECTING]: t`Connecting`,
    [ReadyState.OPEN]: t`Open`,
    [ReadyState.CLOSING]: t`Closing`,
    [ReadyState.CLOSED]: t`Closed`,
    [ReadyState.UNINSTANTIATED]: t`Uninstantiated`
  }[readyState];
  const displayMessages = useMemo(() => {
    return messages.filter((message) => message.type === 'chat_message');
  }, [messages]);

  return (
    <Drawer
      opened={opened}
      size="md"
      position="right"
      onClose={onClose}
      withCloseButton={true}
      styles={{
        header: {
          width: '100%'
        },
        title: {
          width: '100%'
        }
      }}
      title={
        <Group justify="space-between">
          <StylishText size="lg">{t`Live Page Attendance`}</StylishText>{' '}
          <small>
            <IconLink
              size={'1rem'}
              color={readyState == ReadyState.OPEN ? 'green' : 'orange'}
            />
            {connectionStatus}
          </small>
        </Group>
      }
    >
      <Stack gap="xs">
        <Text>
          <Trans>
            Shows users that have this page currently open. All chat is empheral
            and only visible as long as a user is on the page.
          </Trans>
        </Text>
        <Divider />
        <TextInput
          label={t`Message text`}
          value={inputValue}
          onChange={(e) => {
            setInputValue(e.target.value);
          }}
          onKeyDown={(e) => {
            if (e.key === 'Enter') {
              setTimeout(() => {
                handleClickSendMessage();
              }, 200);
            }
          }}
        />
        <Button
          onClick={handleClickSendMessage}
          disabled={readyState !== ReadyState.OPEN}
        >
          <Trans>Send temporary message</Trans>
        </Button>
        <List icon={<></>}>
          {displayMessages.map((message, idx) => (
            <List.Item key={idx}>
              <Text>
                <Pill>{message.user}</Pill>
                {message.message}
              </Text>
            </List.Item>
          ))}
        </List>
      </Stack>
    </Drawer>
  );
}
