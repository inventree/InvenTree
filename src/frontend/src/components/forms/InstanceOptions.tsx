import { t } from '@lingui/core/macro';
import { Trans } from '@lingui/react/macro';
import {
  ActionIcon,
  Button,
  Divider,
  Group,
  Select,
  Text,
  Tooltip
} from '@mantine/core';
import { useToggle } from '@mantine/hooks';
import {
  IconApi,
  IconArrowLeft,
  IconCheck,
  IconCircleCheck,
  IconEdit,
  IconInfoCircle,
  IconPlugConnected,
  IconServer,
  IconServerSpark
} from '@tabler/icons-react';

import type { HostList } from '@lib/types/Server';
import { useShallow } from 'zustand/react/shallow';
import { translateHostName } from '../../defaults/defaultHostList';
import { Wrapper } from '../../pages/Auth/Layout';
import { useLocalState } from '../../states/LocalState';
import { useServerApiState } from '../../states/ServerApiState';
import { ColorToggle } from '../items/ColorToggle';
import { LanguageToggle } from '../items/LanguageToggle';
import { HostOptionsForm } from './HostOptionsForm';

export function InstanceOptions({
  hostKey,
  ChangeHost,
  setHostEdit
}: Readonly<{
  hostKey: string;
  ChangeHost: (newHost: string | null) => void;
  setHostEdit: () => void;
}>) {
  const [hostListEdit, setHostListEdit] = useToggle([false, true] as const);
  const [setHost, setHostList, hostList] = useLocalState(
    useShallow((state) => [state.setHost, state.setHostList, state.hostList])
  );
  const hostListData = Object.keys(hostList).map((key) => ({
    value: key,
    label: translateHostName(hostList[key]?.name)
  }));

  function SaveOptions(newHostList: HostList): void {
    setHostList(newHostList);
    if (newHostList[hostKey] === undefined) {
      setHost('', '');
    }
    setHostListEdit();
  }

  return (
    <Wrapper
      titleText={t`Select Server`}
      smallPadding
      imageOverlay={
        <Group gap={6} align='center' wrap='nowrap'>
          <ColorToggle />
          <LanguageToggle />
        </Group>
      }
    >
      <Text className='auth-welcome-subtitle' mb='sm'>
        <Trans>Choose or configure your backend server connection</Trans>
      </Text>

      <Group gap='xs' justify='space-between' wrap='nowrap' mb='md'>
        <Select
          style={{ flex: 1 }}
          value={hostKey}
          onChange={ChangeHost}
          data={hostListData}
          disabled={hostListEdit}
          comboboxProps={{ transitionProps: { transition: 'pop-top-left' } }}
        />
        <Group gap='xs' wrap='nowrap'>
          <Tooltip label={t`Edit host options`} position='top'>
            <ActionIcon
              className='server-action-icon-btn'
              disabled={hostListEdit}
              onClick={() => setHostListEdit()}
              size={46}
              variant='subtle'
              aria-label={t`Edit host options`}
            >
              <IconEdit size={20} />
            </ActionIcon>
          </Tooltip>
          <Tooltip label={t`Save host selection`} position='top'>
            <ActionIcon
              className='server-action-icon-btn server-action-icon-confirm'
              onClick={setHostEdit}
              disabled={hostListEdit}
              size={46}
              variant='subtle'
              aria-label={t`Save host selection`}
            >
              <IconCircleCheck size={22} />
            </ActionIcon>
          </Tooltip>
        </Group>
      </Group>

      {hostListEdit ? (
        <div style={{ marginTop: 8 }}>
          <Group justify='space-between' mb='sm'>
            <Text fw={600} size='sm' c='#0f172a'>
              <Trans>Edit host options</Trans>
            </Text>
            <Button
              variant='subtle'
              size='xs'
              onClick={() => setHostListEdit()}
              c='#475569'
              leftSection={<IconArrowLeft size={14} />}
            >
              <Trans>Back</Trans>
            </Button>
          </Group>
          <HostOptionsForm data={hostList} saveOptions={SaveOptions} />
        </div>
      ) : (
        <>
          <ServerInfo hostList={hostList} hostKey={hostKey} />
          <Button
            className='auth-submit-btn'
            onClick={setHostEdit}
            mt='lg'
            leftSection={<IconCheck size={18} />}
          >
            <Trans>Confirm & Return to Login</Trans>
          </Button>
        </>
      )}
    </Wrapper>
  );
}

function ServerInfo({
  hostList,
  hostKey
}: Readonly<{
  hostList: HostList;
  hostKey: string;
}>) {
  const [server] = useServerApiState(useShallow((state) => [state.server]));

  const items = [
    {
      key: 'server',
      label: t`Server`,
      value: hostList[hostKey]?.host || '—',
      icon: <IconServer size={18} />
    },
    {
      key: 'name',
      label: t`Name`,
      value: server.instance || '—',
      icon: <IconInfoCircle size={18} />
    },
    {
      key: 'version',
      label: t`Version`,
      value: server.version || '—',
      icon: <IconInfoCircle size={18} />
    },
    {
      key: 'api',
      label: t`API Version`,
      value: server.apiVersion || '—',
      icon: <IconApi size={18} />
    },
    {
      key: 'plugins',
      label: t`Plugins`,
      value: server.plugins_enabled ? t`Enabled` : t`Disabled`,
      icon: <IconPlugConnected size={18} />,
      isStatus: true,
      status: !!server.plugins_enabled
    },
    {
      key: 'worker',
      label: t`Worker`,
      value: server.worker_running ? t`Running` : t`Stopped`,
      icon: <IconServerSpark size={18} />,
      isStatus: true,
      status: !!server.worker_running
    }
  ];

  return (
    <div className='server-info-card'>
      {items.map((item) => (
        <div key={item.key} className='server-info-row'>
          <div className='server-info-left'>
            <div className='server-info-icon-badge'>
              {item.icon}
            </div>
            <span className='server-info-label'>{item.label}</span>
          </div>
          <div className='server-info-value'>
            {item.isStatus ? (
              <span
                className={`server-pill-badge ${
                  item.status ? 'badge-active' : 'badge-inactive'
                }`}
              >
                <span className='status-dot' />
                {item.value}
              </span>
            ) : (
              <span>{item.value}</span>
            )}
          </div>
        </div>
      ))}
    </div>
  );
}
