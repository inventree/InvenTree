import { t } from '@lingui/macro';

import CompanyDetail from './CompanyDetail';

export default function SupplierDetail() {
  return (
    <CompanyDetail
      title={t`Supplier`}
      breadcrumbs={[{ name: t`Purchasing`, url: '/purchasing/' }]}
      last_crumb_url='/purchasing/supplier'
    />
  );
}
