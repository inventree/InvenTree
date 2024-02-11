import { Accordion, Divider, Stack, Text } from '@mantine/core';
import { Control, FieldValues } from 'react-hook-form';

import { ApiFormField, ApiFormFieldType } from './ApiFormField';

export function NestedObjectField({
  control,
  fieldName,
  definition
}: {
  control: Control<FieldValues, any>;
  definition: ApiFormFieldType;
  fieldName: string;
}) {
  return (
    <Accordion defaultValue={'OpenByDefault'} variant="contained">
      <Accordion.Item value={'OpenByDefault'}>
        <Accordion.Control icon={definition.icon}>
          <Text>{definition.label}</Text>
        </Accordion.Control>
        <Accordion.Panel>
          <Divider sx={{ marginTop: '-10px', marginBottom: '10px' }} />
          <Stack spacing="xs">
            {Object.entries(definition.children ?? {}).map(
              ([childFieldName, field]) => (
                <ApiFormField
                  key={childFieldName}
                  fieldName={`${fieldName}.${childFieldName}`}
                  definition={field}
                  control={control}
                />
              )
            )}
          </Stack>
        </Accordion.Panel>
      </Accordion.Item>
    </Accordion>
  );
}
