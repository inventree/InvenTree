import type { ApiFormFieldType } from '@lib/types/Forms';
import { t } from '@lingui/core/macro';

export function TagsField({
  label,
  description
}: Readonly<{
  label?: string;
  description?: string;
}>): ApiFormFieldType {
  return {
    field_type: 'tags',
    label: label ?? t`Tags`,
    description: description ?? t`Tags for this item`
  };
}
