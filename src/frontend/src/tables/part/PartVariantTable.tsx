import { t } from '@lingui/macro';
import { useMemo } from 'react';

import type { TableFilter } from '../Filter';
import { PartListTable } from './PartTable';

/**
 * Display variant parts for the specified parent part
 */
export function PartVariantTable({ part }: Readonly<{ part: any }>) {
  const tableFilters: TableFilter[] = useMemo(() => {
    return [
      {
        name: 'active',
        label: t`Active`,
        description: t`Show active variants`
      },
      {
        name: 'template',
        label: t`Template`,
        description: t`Show template variants`
      },
      {
        name: 'virtual',
        label: t`Virtual`,
        description: t`Show virtual variants`
      },
      {
        name: 'trackable',
        label: t`Trackable`,
        description: t`Show trackable variants`
      }
    ];
  }, []);

  return (
    <PartListTable
      props={{
        enableDownload: false,
        tableFilters: tableFilters,
        params: {
          ancestor: part.pk
        }
      }}
      defaultPartData={{
        ...part,
        variant_of: part.pk,
        is_template: false
      }}
    />
  );
}
