import { t } from '@lingui/macro';

import CompanyDetail from './CompanyDetail';

export default function CustomerDetail() {
  return (
    <CompanyDetail
      title={t`Customer`}
      breadcrumbs={[{ name: t`Sales`, url: '/sales/' }]}
    />
  );
}
