import { t } from '@lingui/macro';
import {
  IconDownload,
  IconFileSpreadsheet,
  IconFileText,
  IconFileTypeCsv
} from '@tabler/icons-react';
import { useMemo } from 'react';

import {
  ActionDropdown,
  type ActionDropdownItem
} from '../components/items/ActionDropdown';

export function DownloadAction({
  downloadCallback
}: Readonly<{
  downloadCallback: (fileFormat: string) => void;
}>) {
  const formatOptions = [
    { value: 'csv', label: t`CSV`, icon: <IconFileTypeCsv /> },
    { value: 'tsv', label: t`TSV`, icon: <IconFileText /> },
    { value: 'xlsx', label: t`Excel (.xlsx)`, icon: <IconFileSpreadsheet /> }
  ];

  const actions: ActionDropdownItem[] = useMemo(() => {
    return formatOptions.map((format) => ({
      name: format.label,
      icon: format.icon,
      onClick: () => downloadCallback(format.value)
    }));
  }, [formatOptions, downloadCallback]);

  return (
    <ActionDropdown
      tooltip={t`Download Data`}
      icon={<IconDownload />}
      actions={actions}
    />
  );
}
