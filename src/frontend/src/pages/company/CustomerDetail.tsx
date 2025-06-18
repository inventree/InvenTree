import { t } from '@lingui/core/macro';

import CompanyDetail from './CompanyDetail';

export default function CustomerDetail() {
  return (
    <CompanyDetail
      title={t`Customer`}
      breadcrumbs={[{ name: t`Sales`, url: '/sales/' }]}
      last_crumb_url='/sales/customer'
    />
  );
}
