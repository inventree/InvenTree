import { ModelInformationDict } from '../components/render/ModelType';
import { ModelType } from '../enums/ModelType';

/**
 * Returns the detail view URL for a given model type
 */
export function getDetailUrl(model: ModelType, pk: number | string): string {
  const modelInfo = ModelInformationDict[model];

  if (!!pk && modelInfo && modelInfo.url_detail) {
    return modelInfo.url_detail.replace(':pk', pk.toString());
  }

  console.error(`No detail URL found for model ${model}!`);
  return '';
}
