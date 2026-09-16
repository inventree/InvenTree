import { Alert } from '@mantine/core';
import {
  INVENTREE_PLUGIN_VERSION,
  type InvenTreePluginContext
} from '../types/Plugins';
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
  if (!context?.tables?.renderTable) {
    return (
      <Alert title='Plugin Version Error' color='red'>
        {
          'The <InvenTreeTable> component cannot be rendered because the plugin context is missing the "renderTable" function.'
        }
        <br />
        {
          'This means that the InvenTree UI library version is incompatible with this plugin version.'
        }
        <br />
        <b>Plugin Version:</b> {INVENTREE_PLUGIN_VERSION}
        <br />
        <b>UI Version:</b> {context?.version?.inventree || 'unknown'}
        <br />
      </Alert>
    );
  }

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
