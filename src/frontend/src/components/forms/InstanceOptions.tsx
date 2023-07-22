import { Trans } from '@lingui/macro';
import { Divider, Group, Select, Text, Title } from '@mantine/core';
import { useToggle } from '@mantine/hooks';
import { IconCheck } from '@tabler/icons-react';

import { useLocalState } from '../../states/LocalState';
import { HostList } from '../../states/states';
import { EditButton } from '../items/EditButton';
import { HostOptionsForm } from './HostOptionsForm';

export function InstanceOptions({
  hostKey,
  ChangeHost,
  setHostEdit
}: {
  hostKey: string;
  ChangeHost: (newHost: string) => void;
  setHostEdit: () => void;
}) {
  const [HostListEdit, setHostListEdit] = useToggle([false, true] as const);
  const [setHost, setHostList, hostList] = useLocalState((state) => [
    state.setHost,
    state.setHostList,
    state.hostList
  ]);

  const hostListData = Object.keys(hostList).map((key) => ({
    value: key,
    label: hostList[key].name
  }));

  function SaveOptions(newHostList: HostList): void {
    setHostList(newHostList);
    if (newHostList[hostKey] === undefined) {
      setHost('', '');
    }
    setHostListEdit();
  }

  return (
    <>
      <Title order={3}>
        <Trans>Select destination instance</Trans>
      </Title>
      <Group>
        <Group>
          <Select
            value={hostKey}
            onChange={ChangeHost}
            data={hostListData}
            disabled={HostListEdit}
          />
          <EditButton
            setEditing={setHostListEdit}
            editing={HostListEdit}
            disabled={HostListEdit}
          />
        </Group>
        <EditButton
          setEditing={setHostEdit}
          editing={true}
          disabled={HostListEdit}
          saveIcon={<IconCheck />}
        />
      </Group>
      {HostListEdit && (
        <>
          <Divider my={'sm'} />
          <Text>
            <Trans>Edit possible host options</Trans>
          </Text>
          <HostOptionsForm data={hostList} saveOptions={SaveOptions} />
        </>
      )}
    </>
  );
}
