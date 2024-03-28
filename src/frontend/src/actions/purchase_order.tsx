import { t } from '@lingui/macro';
import { IconBasketCheck } from '@tabler/icons-react';

import { ActionFunctionType, ActionType } from '.';
import { api } from '../App';

function receiveOrder(props: ActionFunctionType) {
  const { barcode } = props;
  api.post('/api/barcode/po-receive/', { barcode }).then((response) => {
    console.log(response);
  });
}

export const purchase_orderActions: ActionType[] = [
  {
    title: t`Receive order`,
    function: receiveOrder,
    icon: <IconBasketCheck />
  }
];
