import type { InvenTreePluginContext } from '../types/Plugins';
import type {
  InvenTreeTableProps,
  TableColumn,
  TableState
} from '../types/Tables';

/**
 * Wrapper function which allows plugins to render an InvenTree component instance directly,
 * in a similar way to the standard InvenTreeTable component.
 *
 * Note: The InventreePluginContext "context" object must be provided when rendering the table
 *
 */

export default function InvenTreeTable({
  url,
  tableState,
  tableData,
  columns,
  props,
  context
}: {
  url?: string;
  tableState: TableState;
  tableData?: any[];
  columns: TableColumn<any>[];
  props: InvenTreeTableProps;
  context: InvenTreePluginContext;
}) {
  return context?.tables.renderTable({
    url: url,
    tableState: tableState,
    tableData: tableData,
    columns: columns,
    props: props,
    api: context.api,
    navigate: context.navigate
  });
}
