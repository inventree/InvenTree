import {
  ModelInformationDict,
  type ModelInformationInterface
} from '@lib/enums/ModelInformation';
import type { ModelType } from '@lib/enums/ModelType';

/*
 * Extract model definition given the provided type - returns translatable strings for labels as string, not functions
 * @param type - ModelType to extract information from
 * @returns ModelInformationInterface
 */
export function getModelInfo(type: ModelType): ModelInformationInterface {
  return {
    ...ModelInformationDict[type],
    label: ModelInformationDict[type].label(),
    label_multiple: ModelInformationDict[type].label_multiple()
  };
}
