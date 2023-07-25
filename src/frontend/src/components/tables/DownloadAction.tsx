import { Trans, t } from '@lingui/macro';
import { ActionIcon, Divider, Group, Menu, Select } from '@mantine/core';
import { Tooltip } from '@mantine/core';
import { Button, Modal, Stack } from '@mantine/core';
import { useDisclosure } from '@mantine/hooks';
import { IconDownload } from '@tabler/icons-react';
import { useState } from 'react';

export function DownloadAction({
  downloadCallback
}: {
  downloadCallback: (fileFormat: string) => void;
}) {
  const formatOptions = [
    { value: 'csv', label: t`CSV` },
    { value: 'tsv', label: t`TSV` },
    { value: 'xlsx', label: t`Excel` }
  ];

  return (
    <>
      <Menu>
        <Menu.Target>
          <ActionIcon>
            <Tooltip label={t`Download selected data`}>
              <IconDownload />
            </Tooltip>
          </ActionIcon>
        </Menu.Target>
        <Menu.Dropdown>
          {formatOptions.map((format) => (
            <Menu.Item
              key={format.value}
              onClick={() => {
                downloadCallback(format.value);
              }}
            >
              {format.label}
            </Menu.Item>
          ))}
        </Menu.Dropdown>
      </Menu>
    </>
  );
}
