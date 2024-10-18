import { ModelInformationDict } from '../components/render/ModelType';
import type { ModelType } from '../enums/ModelType';
import { base_url } from '../main';

/**
 * Returns the detail view URL for a given model type
 */
export function getDetailUrl(
  model: ModelType,
  pk: number | string,
  absolute?: boolean
): string {
  const modelInfo = ModelInformationDict[model];

  if (pk === undefined || pk === null) {
    return '';
  }

  if (!!pk && modelInfo && modelInfo.url_detail) {
    const url = modelInfo.url_detail.replace(':pk', pk.toString());
    const base = base_url;

    if (absolute && base) {
      return `/${base}${url}`;
    } else {
      return url;
    }
  }

  console.error(`No detail URL found for model ${model} <${pk}>`);
  return '';
}
