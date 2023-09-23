import { Trans } from '@lingui/macro';

import { StylishText } from '../../components/items/StylishText';
import { ApprovalTable } from '../../components/tables/approval/ApprovalTable';

export default function ApprovalIndex() {
  return (
    <>
      <StylishText>
        <Trans>Approvals</Trans>
      </StylishText>
      <ApprovalTable params={{}} tableKey={'approval'} />
    </>
  );
}
