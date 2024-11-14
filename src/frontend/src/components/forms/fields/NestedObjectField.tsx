import { Accordion, Divider, Stack, Text } from '@mantine/core';
import type { Control, FieldValues } from 'react-hook-form';

import {
  ApiFormField,
  type ApiFormFieldSet,
  type ApiFormFieldType
} from './ApiFormField';

export function NestedObjectField({
  control,
  fieldName,
  definition,
  url,
  setFields
}: Readonly<{
  control: Control<FieldValues, any>;
  definition: ApiFormFieldType;
  fieldName: string;
  url?: string;
  setFields?: React.Dispatch<React.SetStateAction<ApiFormFieldSet>>;
}>) {
  return (
    <Accordion defaultValue={'OpenByDefault'} variant='contained'>
      <Accordion.Item value={'OpenByDefault'}>
        <Accordion.Control icon={definition.icon}>
          <Text>{definition.label}</Text>
        </Accordion.Control>
        <Accordion.Panel>
          <Divider style={{ marginTop: '-10px', marginBottom: '10px' }} />
          <Stack gap='xs'>
            {Object.entries(definition.children ?? {}).map(
              ([childFieldName, field]) => (
                <ApiFormField
                  key={childFieldName}
                  fieldName={`${fieldName}.${childFieldName}`}
                  definition={field}
                  control={control}
                  url={url}
                  setFields={setFields}
                />
              )
            )}
          </Stack>
        </Accordion.Panel>
      </Accordion.Item>
    </Accordion>
  );
}
