import { t } from '@lingui/core/macro';
import { DetailsTable } from '../../components/details/Details';

export function LocationTypeDetailsPanel({
  instance
}: Readonly<{ instance: any }>) {
  return (
    <DetailsTable
      item={instance}
      fields={[
        { type: 'text', name: 'name', label: t`Name`, copy: true },
        { type: 'text', name: 'description', label: t`Description` },
        {
          type: 'number',
          name: 'location_count',
          label: t`Stock Locations`,
          icon: 'location'
        }
      ]}
    />
  );
}
