import { UserRoles } from '@lib/index';
import type { UseModalReturn } from '@lib/types/Modals';
import { t } from '@lingui/core/macro';
import { useMemo } from 'react';
import type { ActionDropdownItem } from '../components/items/ActionDropdown';
import {
  type StockOperationProps,
  useAddStockItem,
  useAssignStockItem,
  useChangeStockStatus,
  useCountStockItem,
  useDeleteStockItem,
  useMergeStockItem,
  useRemoveStockItem,
  useTransferStockItem
} from '../forms/StockForms';
import { InvenTreeIcon } from '../functions/icons';
import { useUserState } from '../states/UserState';

interface StockAdjustActionProps {
  formProps: StockOperationProps;
  add?: boolean;
  assign?: boolean;
  count?: boolean;
  changeStatus?: boolean;
  delete?: boolean;
  merge?: boolean;
  remove?: boolean;
  transfer?: boolean;
}

interface StockAdjustActionReturnProps {
  modals: UseModalReturn[];
  menuActions: ActionDropdownItem[];
}

/**
 * Hook to provide an interface for stock transfer actions.
 * - Provides a set of modals for creating, editing, and deleting stock transfers.
 * - Provides a set of menu actions for opening the modals.
 */

export function useStockAdjustActions(
  props: StockAdjustActionProps
): StockAdjustActionReturnProps {
  const user = useUserState();

  // The available modals for stock adjustment actions
  const addStock = useAddStockItem(props.formProps);
  const assignStock = useAssignStockItem(props.formProps);
  const countStock = useCountStockItem(props.formProps);
  const changeStatus = useChangeStockStatus(props.formProps);
  const deleteStock = useDeleteStockItem(props.formProps);
  const mergeStock = useMergeStockItem(props.formProps);
  const removeStock = useRemoveStockItem(props.formProps);
  const transferStock = useTransferStockItem(props.formProps);

  const modals: UseModalReturn[] = useMemo(() => {
    const modals: UseModalReturn[] = [];

    if (!user.hasChangeRole(UserRoles.stock)) {
      return [];
    }

    props.add != false && modals.push(addStock);
    props.assign != false && modals.push(assignStock);
    props.count != false && modals.push(countStock);
    props.changeStatus != false && modals.push(changeStatus);
    props.merge != false && modals.push(mergeStock);
    props.remove != false && modals.push(removeStock);
    props.transfer != false && modals.push(transferStock);
    props.delete != false &&
      user.hasDeleteRole(UserRoles.stock) &&
      modals.push(deleteStock);

    return modals;
  }, [props, user]);

  const menuActions: ActionDropdownItem[] = useMemo(() => {
    const menuActions: ActionDropdownItem[] = [];

    if (!user.hasChangeRole(UserRoles.stock)) {
      return [];
    }

    props.count != false &&
      menuActions.push({
        name: t`Count Stock`,
        icon: <InvenTreeIcon icon='stocktake' iconProps={{ color: 'blue' }} />,
        tooltip: t`Count selected stock items`,
        onClick: () => {
          countStock.open();
        }
      });

    props.add != false &&
      menuActions.push({
        name: t`Add Stock`,
        icon: <InvenTreeIcon icon='add' iconProps={{ color: 'green' }} />,
        tooltip: t`Add to selected stock items`,
        onClick: () => {
          addStock.open();
        }
      });

    props.remove != false &&
      menuActions.push({
        name: t`Remove Stock`,
        icon: <InvenTreeIcon icon='remove' iconProps={{ color: 'red' }} />,
        tooltip: t`Remove from selected stock items`,
        onClick: () => {
          removeStock.open();
        }
      });

    props.transfer != false &&
      menuActions.push({
        name: t`Transfer Stock`,
        icon: <InvenTreeIcon icon='transfer' iconProps={{ color: 'blue' }} />,
        tooltip: t`Transfer selected stock items`,
        onClick: () => {
          transferStock.open();
        }
      });

    props.merge != false &&
      menuActions.push({
        name: t`Merge Stock`,
        icon: <InvenTreeIcon icon='merge' />,
        tooltip: t`Merge selected stock items`,
        onClick: () => {
          mergeStock.open();
        }
      });

    props.changeStatus != false &&
      menuActions.push({
        name: t`Change Status`,
        icon: <InvenTreeIcon icon='info' iconProps={{ color: 'blue' }} />,
        tooltip: t`Change status of selected stock items`,
        onClick: () => {
          changeStatus.open();
        }
      });

    props.assign != false &&
      menuActions.push({
        name: t`Assign Stock`,
        icon: <InvenTreeIcon icon='customer' />,
        tooltip: t`Assign selected stock items to a customer`,
        onClick: () => {
          assignStock.open();
        }
      });

    props.delete != false &&
      menuActions.push({
        name: t`Delete Stock`,
        icon: <InvenTreeIcon icon='delete' iconProps={{ color: 'red' }} />,
        tooltip: t`Delete selected stock items`,
        disabled: !user.hasDeleteRole(UserRoles.stock),
        onClick: () => {
          deleteStock.open();
        }
      });

    return menuActions;
  }, [props, user]);

  return {
    modals,
    menuActions
  };
}
