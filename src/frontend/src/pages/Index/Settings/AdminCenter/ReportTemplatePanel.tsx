import { t } from '@lingui/macro';

import { Accordion } from '@mantine/core';
import { useMemo } from 'react';
import { YesNoButton } from '../../../../components/buttons/YesNoButton';
import { AttachmentLink } from '../../../../components/items/AttachmentLink';
import { StylishText } from '../../../../components/items/StylishText';
import { ApiEndpoints } from '../../../../enums/ApiEndpoints';
import { ModelType } from '../../../../enums/ModelType';
import { useTable } from '../../../../hooks/UseTable';
import { apiUrl } from '../../../../states/ApiState';
import type { TableColumn } from '../../../../tables/Column';
import { DateColumn } from '../../../../tables/ColumnRenderers';
import { InvenTreeTable } from '../../../../tables/InvenTreeTable';
import { TemplateTable } from '../../../../tables/settings/TemplateTable';

function ReportTemplateTable() {
  return (
    <TemplateTable
      templateProps={{
        modelType: ModelType.reporttemplate,
        templateEndpoint: ApiEndpoints.report_list,
        printingEndpoint: ApiEndpoints.report_print,
        additionalFormFields: {
          page_size: {
            label: t`Page Size`
          },
          landscape: {
            label: t`Landscape`,
            modelRenderer: (instance: any) => (
              <YesNoButton value={instance.landscape} />
            )
          },
          attach_to_model: {
            label: t`Attach to Model`,
            modelRenderer: (instance: any) => (
              <YesNoButton value={instance.attach_to_model} />
            )
          }
        }
      }}
    />
  );
}

function ReportOutputTable() {
  const table = useTable('report-output');

  const tableColumns: TableColumn[] = useMemo(() => {
    return [
      {
        accessor: 'output',
        sortable: false,
        switchable: false,
        title: t`Report Output`,
        noWrap: true,
        noContext: true,
        render: (record: any) => {
          if (record.output) {
            return <AttachmentLink attachment={record.output} />;
          } else {
            return '-';
          }
        }
      },
      {
        accessor: 'model_type',
        sortable: false,
        switchable: false,
        title: t`Model Type`
      },
      DateColumn({
        accessor: 'created',
        title: t`Creation Date`,
        switchable: false,
        sortable: false
      }),
      {
        accessor: 'user_detail.username',
        title: t`Created By`
      }
    ];
  }, []);

  return (
    <>
      <InvenTreeTable
        url={apiUrl(ApiEndpoints.report_output)}
        tableState={table}
        columns={tableColumns}
        props={{
          enableSearch: false,
          enableColumnSwitching: false,
          enableSelection: true,
          enableBulkDelete: true
        }}
      />
    </>
  );
}

export default function ReportTemplatePanel() {
  return (
    <Accordion defaultValue='templates'>
      <Accordion.Item value='templates'>
        <Accordion.Control>
          <StylishText size='lg'>{t`Report Templates`}</StylishText>
        </Accordion.Control>
        <Accordion.Panel>
          <ReportTemplateTable />
        </Accordion.Panel>
      </Accordion.Item>
      <Accordion.Item value='outputs'>
        <Accordion.Control>
          <StylishText size='lg'>{t`Report Outputs`}</StylishText>
        </Accordion.Control>
        <Accordion.Panel>
          <ReportOutputTable />
        </Accordion.Panel>
      </Accordion.Item>
    </Accordion>
  );
}
