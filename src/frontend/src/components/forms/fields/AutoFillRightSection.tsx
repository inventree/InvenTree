import { t } from '@lingui/core/macro';
import { Tooltip } from '@mantine/core';
import { IconCopyCheck, IconX } from '@tabler/icons-react';

/**
 * Custom "RightSection" component for form fields,
 * to implement functionality such as:
 *
 * - Clear field value
 * - Auto-fill with suggested placeholder
 */
export default function AutoFillRightSection({
  value,
  fieldName,
  definition,
  onChange
}: {
  value: any;
  fieldName: string;
  definition: any;
  placeholderAutofill?: boolean;
  onChange: (value: any) => void;
}) {
  if (definition.rightSection) {
    // Use the specified override value
    return definition.rightSection;
  }

  if (value) {
    // If a value is provided, render a button to clear the field
    if (!definition.required && !definition.disabled) {
      const emptyValue = definition.allow_null ? null : '';
      return (
        <Tooltip label={t`Clear`} position='top-end'>
          <IconX
            aria-label={`field-${fieldName}-clear`}
            size='1rem'
            color='red'
            onClick={() => onChange(emptyValue)}
          />
        </Tooltip>
      );
    }
  } else if (!value && definition.placeholder && !definition.disabled) {
    // Render auto-fill button
    return (
      <Tooltip label={t`Accept suggested value`} position='top-end'>
        <IconCopyCheck
          aria-label={`field-${fieldName}-accept-placeholder`}
          size='1rem'
          color='green'
          onClick={() => onChange(definition.placeholder)}
        />
      </Tooltip>
    );
  }
}
