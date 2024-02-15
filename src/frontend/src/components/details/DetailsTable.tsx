import { Group, Table } from '@mantine/core';

import { DetailsField, FieldValueType } from './DetailsField';
import { DetailsValue } from './DetailsValue';
import { PartIcons } from './PartIcons';

/*
 * Render a table of "details fields" in the "details view" of a given page.
 * This is used to provide a consistent layout for the details view.
 */
export function DetailsTable({
  item,
  fields,
  partIcons = false
}: {
  item: any;
  fields: DetailsField[][];
  partIcons?: boolean;
}) {
  return (
    <Group>
      <Table striped>
        <tbody>
          {partIcons && (
            <tr>
              <PartIcons
                assembly={item.assembly}
                template={item.is_template}
                component={item.component}
                trackable={item.trackable}
                purchaseable={item.purchaseable}
                saleable={item.salable}
                virtual={item.virtual}
                active={item.active}
              />
            </tr>
          )}
          {fields.map((data: DetailsField[], index: number) => {
            let value: FieldValueType[] = [];
            for (const val of data) {
              if (val.value_formatter) {
                value.push(undefined);
              } else {
                value.push(item[val.name]);
              }
            }

            return (
              <DetailsValue
                field_data={data}
                field_value={value}
                key={index}
                unit={item.units}
              />
            );
          })}
        </tbody>
      </Table>
    </Group>
  );
}
