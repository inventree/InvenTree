import { t } from '@lingui/core/macro';

import CompanyDetail from './CompanyDetail';

export default function ManufacturerDetail() {
  return (
    <CompanyDetail
      title={t`Manufacturer`}
      breadcrumbs={[{ name: t`Purchasing`, url: '/purchasing/' }]}
      last_crumb_url='/purchasing/manufacturer'
    />
  );
}
