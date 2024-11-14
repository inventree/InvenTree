import { t } from '@lingui/macro';
import DashboardLayout from '../../components/dashboard/DashboardLayout';
import PageTitle from '../../components/nav/PageTitle';

export default function Home() {
  return (
    <>
      <PageTitle title={t`Dashboard`} />
      <DashboardLayout />
    </>
  );
}
