import { IconUsers } from "@tabler/icons-react";
import { useCallback, useEffect, useMemo, useState } from "react";

import { ApiEndpoints } from "@lib/enums/ApiEndpoints";
import { ModelType } from "@lib/enums/ModelType";
import { apiUrl } from "@lib/functions/Api";
import type { ApiFormFieldSet, ApiFormFieldType } from "@lib/types/Forms";
import type {
  StatusCodeInterface,
  StatusCodeListInterface,
} from "../shared/render/StatusRenderer";
import { useApi } from "@context/ApiContext";
import { useGlobalStatusState } from "@store/GlobalStatusState";
import { useUserState } from "@store/UserState";
import { ProjectCodeField } from "./CommonFields";

export function projectCodeFields(): ApiFormFieldSet {
  return {
    code: {},
    description: {},
    responsible: {
      icon: <IconUsers />,
    },
    active: {},
  };
}

export function metalTypeFields(): ApiFormFieldSet {
  return {
    code: {},
    name: {},
    description: {},
    active: {},
  };
}

export function stonePlaceFields(): ApiFormFieldSet {
  return {
    name: {},
    description: {},
    active: {},
  };
}

export function metalPurityFields(): ApiFormFieldSet {
  return {
    metal_type: {
      api_url: `${apiUrl(ApiEndpoints.metal_type_list)}?active=true`,
      modelRenderer: (arg: any) => {
        const instance = arg?.instance ?? arg;
        return instance?.name ?? (instance?.name ? `#${instance.name}` : "");
      },
    },
    name: {},
    purity: {},
    active: {},
  };
}

export function metalRate(): ApiFormFieldSet {
  return {
    metal_type: {
      api_url: `${apiUrl(ApiEndpoints.metal_type_list)}?active=true`,
      modelRenderer: (arg: any) => {
        const instance = arg?.instance ?? arg;
        return instance?.name ?? (instance?.name ? `#${instance.name}` : "");
      },
    },
    rate: {},
    date: {},
    active: {},
  };
}

export function masterTerms(): ApiFormFieldSet {
  return {
    name: {},
    days: {},
    description: {},
    active: {},
    vendors: {
      field_type: "related field",
      model: ModelType.company,
      multiple: true,
      api_url: apiUrl(ApiEndpoints.company_list),
      filters: { is_supplier: true },
      disableWhen: (values: any) => !!values?.all_vendors,
      modelRenderer: (arg: any) => {
        const instance = arg?.instance ?? arg;
        return instance?.code ?? "";
      },
    },
    all_vendors: {},
  };
}

export function masterCourierService(): ApiFormFieldSet {
  return {
    name: {},
    contact_person: {},
    phone: {},
    email: {},
    tracking_url: {},
    active: {},
  };
}

export function masterExecutive(): ApiFormFieldSet {
  return {
    name: {},
    code: {},
    email: {},
    phone: {},
    active: {},
  };
}
export function findingTypeFields(): ApiFormFieldSet {
  return {
    name: {},
    description: {},
    type: {},
    weight: {},
    metal: {},
    price: {},
    active: {},
  };
}

export function finishTypeFields(): ApiFormFieldSet {
  return {
    name: {},
    description: {},
    active: {},
  };
}

export function ListDutyFields(): ApiFormFieldSet {
  return {
    metal_type: {
      api_url: `${apiUrl(ApiEndpoints.metal_type_list)}?active=true`,
      modelRenderer: (arg: any) => {
        const instance = arg?.instance ?? arg;
        // return instance?.name ?? (instance?.pk ? `#${instance.pk}` : "");
        return instance?.name ?? (instance?.name ? `#${instance.name}` : "");
      },
    },
    duty: {},
    markup: {},
    description: {},
    active: {},
  };
}

export function MasterSettingFields(): ApiFormFieldSet {
  return {
    name: {},
    description: {},
    active: {},
  };
}

export function LabourSettingFields(): ApiFormFieldSet {
  return {
    name: {},
    setting: {
      api_url: apiUrl(ApiEndpoints.master_setting),
      modelRenderer: (arg: any) => {
        const instance = arg?.instance ?? arg;
        return instance?.name ?? (instance?.name ? `#${instance.name}` : "");
      },
    },
    charge_type: {},
    rate: {},
    active: {},
  };
}

export function masterVendors(): ApiFormFieldSet {
  return {
    code: {},
    name: {},
    description: {},
    website: {},
    phone: {},
    email: {},
    contact: {},
    link: {},
    is_customer: {
      hidden: true,
      value: false,
    },
    is_supplier: {
      hidden: true,
      value: true,
    },
    is_manufacturer: {
      hidden: true,
      value: false,
    },
    tax_id: {},
    fax: {},
    city: {},
    state: {},
    country: {},
    rating: {},
    credit_limit: {},
    ref_by: {},
    active: {},
  };
}
export function vendorContactFields(): ApiFormFieldSet {
  return {
    company: { hidden: true },
    name: {},
    phone: {},
    mobile: {},
    email: {},
    role: {},
  };
}

export function customerContactFields(): ApiFormFieldSet {
  return {
    company: { hidden: true },
    name: {},
    phone: {},
    mobile: {},
    email: {},
    role: {},
  };
}

export function masterCustomer(): ApiFormFieldSet {
  return {
    code: {},
    name: {},
    description: {},
    website: {},
    phone: {},
    email: {},
    contact: {},
    link: {},
    is_customer: {
      hidden: true,
      value: true,
    },
    is_supplier: {
      hidden: true,
      value: false,
    },
    is_manufacturer: {
      hidden: true,
      value: false,
    },
    tax_id: {},
    fax: {},
    city: {},
    state: {},
    country: {},
    rating: {},
    credit_limit: {},
    ref_by: {},
    active: {},
  };
}

export function jewelleryCategoryFields(): ApiFormFieldSet {
  return {
    name: {},
    description: {},
    active: {},
  };
}

export function jewellerySubCategoryFields(): ApiFormFieldSet {
  return {
    category: {
      api_url: apiUrl(ApiEndpoints.jewellery_category),
      modelRenderer: (arg: any) => {
        const instance = arg?.instance ?? arg;
        return instance?.name ?? (instance?.name ? `#${instance.name}` : "");
      },
    },
    name: {},
    description: {},
    active: {},
  };
}

export function colorStoneTypeFields(): ApiFormFieldSet {
  return {
    name: {},
    description: {},
    active: {},
  };
}

export function colorStoneCutFields(): ApiFormFieldSet {
  return {
    name: {},
    description: {},
    active: {},
  };
}

export function colorStoneShapeFields(): ApiFormFieldSet {
  return {
    name: {},
    description: {},
    active: {},
  };
}

export function colorStoneColorFields(): ApiFormFieldSet {
  return {
    name: {},
    description: {},
    active: {},
  };
}

export function colorStoneSizeFields(): ApiFormFieldSet {
  return {
    name: {},
    mm_size: {},
    sieve_size: {},
    description: {},
    active: {},
  };
}

export function colorStoneQualityFields(): ApiFormFieldSet {
  return {
    name: {},
    description: {},
    active: {},
  };
}

export function colorStoneRateFields(): ApiFormFieldSet {
  return {
    shape: {
      api_url: `${apiUrl(ApiEndpoints.color_stone_shape_list)}?active=true`,
      modelRenderer: (arg: any) => {
        const instance = arg?.instance ?? arg;
        return instance?.name ?? (instance?.name ? `#${instance.name}` : "");
      },
    },
    mm_size: {
      api_url: `${apiUrl(ApiEndpoints.color_stone_size_list)}?active=true`,
      modelRenderer: (arg: any) => {
        const instance = arg?.instance ?? arg;
        return instance?.name ?? (instance?.name ? `#${instance.name}` : "");
      },
    },
    stone: {
      api_url: `${apiUrl(ApiEndpoints.color_stone_type_list)}?active=true`,
      modelRenderer: (arg: any) => {
        const instance = arg?.instance ?? arg;
        return instance?.name ?? (instance?.name ? `#${instance.name}` : "");
      },
    },
    color: {
      api_url: `${apiUrl(ApiEndpoints.color_stone_color_list)}?active=true`,
      modelRenderer: (arg: any) => {
        const instance = arg?.instance ?? arg;
        return instance?.name ?? (instance?.name ? `#${instance.name}` : "");
      },
    },
    cut: {
      api_url: `${apiUrl(ApiEndpoints.color_stone_cut_list)}?active=true`,
      modelRenderer: (arg: any) => {
        const instance = arg?.instance ?? arg;
        return instance?.name ?? (instance?.name ? `#${instance.name}` : "");
      },
    },
    quality: {
      api_url: `${apiUrl(ApiEndpoints.color_stone_quality_list)}?active=true`,
      modelRenderer: (arg: any) => {
        const instance = arg?.instance ?? arg;
        return instance?.name ?? (instance?.name ? `#${instance.name}` : "");
      },
    },
    pointer: {},
    rate: {},
    pc: {},
    customers: {
      field_type: "related field",
      model: ModelType.company,
      multiple: true,
      api_url: apiUrl(ApiEndpoints.company_list),
      filters: { is_customer: true },
      disableWhen: (values: any) => !!values?.all_customers,
      modelRenderer: (arg: any) => {
        const instance = arg?.instance ?? arg;
        return instance?.code ?? "";
      },
    },
    all_customers: {},
    active: {},
  };
}

export function stampFields(
  includeImage: boolean = true,
  onImageChange?: (file: File | null) => void,
): ApiFormFieldSet {
  const fields: ApiFormFieldSet = {
    name: {},
    description: {},
    customers: {
      field_type: "related field",
      model: ModelType.company,
      multiple: true,
      api_url: apiUrl(ApiEndpoints.company_list),
      filters: { is_customer: true },
      disableWhen: (values: any) => !!values?.all_customers,
      modelRenderer: (arg: any) => {
        const instance = arg?.instance ?? arg;
        return instance?.code ?? "";
      },
    },
    all_customers: {},
    active: {},
  };

  if (includeImage) {
    fields.image = {
      field_type: "file upload",
      onValueChange: (value: any) => {
        onImageChange?.(value instanceof File ? value : null);
      },
    };
  }

  return fields;
}

// Cost Card is edited as a full page with a tab per section (see
// containers/cost-card-detail) rather than a single modal, so its fields are
// split into one set per tab instead of one flat costCardFields() blob.

/** General tab — core identity, party, and measurement fields. */
export function costCardGeneralFields(): ApiFormFieldSet {
  return {
    cost_card_no: { read_only: true },
    our_style_no: {},
    vendor_style_no: {},
    vendor: {
      api_url: `${apiUrl(ApiEndpoints.master_vendor_customer)}?active=true&is_supplier=true`,
      modelRenderer: (arg: any) => {
        const instance = arg?.instance ?? arg;
        return instance?.code ?? (instance?.code ? `#${instance.code}` : "");
      },
    },
    customer: {
      api_url: `${apiUrl(ApiEndpoints.master_vendor_customer)}?active=true&is_customer=true`,
      modelRenderer: (arg: any) => {
        const instance = arg?.instance ?? arg;
        return instance?.code ?? (instance?.code ? `#${instance.code}` : "");
      },
    },
    category: {
      api_url: `${apiUrl(ApiEndpoints.jewellery_category)}?active=true`,
      modelRenderer: (arg: any) => {
        const instance = arg?.instance ?? arg;
        return instance?.name ?? (instance?.name ? `#${instance.name}` : "");
      },
    },
    sub_category: {
      api_url: `${apiUrl(ApiEndpoints.jewellery_sub_category)}?active=true`,
      modelRenderer: (arg: any) => {
        const instance = arg?.instance ?? arg;
        return instance?.name ?? (instance?.name ? `#${instance.name}` : "");
      },
    },
    metal_purity: {
      api_url: `${apiUrl(ApiEndpoints.metal_purity_list)}?active=true`,
      modelRenderer: (arg: any) => {
        const instance = arg?.instance ?? arg;
        return instance?.name ?? (instance?.name ? `#${instance.name}` : "");
      },
    },
    karat: {},
    metal_grams: {},
    finding_type: {
      api_url: `${apiUrl(ApiEndpoints.finding_type)}?active=true`,
      modelRenderer: (arg: any) => {
        const instance = arg?.instance ?? arg;
        return instance?.name ?? (instance?.name ? `#${instance.name}` : "");
      },
    },
    finding_price: {},
    gross_weight: {},
    net_weight: {},
    troy_ounce_price: {},
    height_mm: {},
    height_inch: {},
    length_mm: {},
    length_inch: {},
    width_mm: {},
    width_inch: {},
    shank_size_mm: {},
    shank_size_inch: {},
    drape_length_mm: {},
    drape_length_inch: {},
    design_note: {},
    special_note: {},
    remarks: {},
    active: {},
  };
}

/** Labour Details tab — read-only rollups from the Finish / Diamond / Color Stone tabs. */
export function costCardLabourFields(): ApiFormFieldSet {
  return {
    labour_finish_amount: { read_only: true },
    labour_diamond_amount: { read_only: true },
    labour_colorstone_amount: { read_only: true },
  };
}

/** Cost tab — editable percentages plus their computed (read-only) amounts. */
export function costCardCostFields(): ApiFormFieldSet {
  return {
    metal_loss_pct: {},
    metal_loss_amount: { read_only: true },
    metal_amount: { read_only: true },
    dia_pcs: { read_only: true },
    dia_cts: { read_only: true },
    dia_amount: { read_only: true },
    col_pcs: { read_only: true },
    col_cts: { read_only: true },
    col_amount: { read_only: true },
    stone_pcs: { read_only: true },
    stone_cts: { read_only: true },
    stone_amount: { read_only: true },
    labour_amount: { read_only: true },
    finding_price: { read_only: true },
    dia_handling_pct: {},
    dia_handling_amount: { read_only: true },
    col_handling_pct: {},
    col_handling_amount: { read_only: true },
    vendor_markup_pct: {},
    vendor_markup_amount: { read_only: true },
    fob: { read_only: true },
    duty_pct: {},
    duty_amount: { read_only: true },
    margin_pct: {},
    margin_amount: { read_only: true },
    final_amount: { read_only: true },
  };
}

/** Remarks tab — the detailed remarks field (distinct from the short General-tab remarks). */
export function costCardRemarksFields(): ApiFormFieldSet {
  return {
    remarks_full: {},
  };
}

/** Shared dropdown field definitions for a diamond/color-stone cost card line. */
function costCardStoneLineFields(
  stoneEndpoint: ApiEndpoints,
  shapeEndpoint: ApiEndpoints,
  sizeEndpoint: ApiEndpoints,
  colorEndpoint: ApiEndpoints,
  cutEndpoint: ApiEndpoints,
  qualityEndpoint: ApiEndpoints,
): ApiFormFieldSet {
  const nameRenderer = (arg: any) => {
    const instance = arg?.instance ?? arg;
    return instance?.name ?? "";
  };

  return {
    stone: {
      api_url: `${apiUrl(stoneEndpoint)}?active=true`,
      modelRenderer: nameRenderer,
    },
    shape: {
      api_url: `${apiUrl(shapeEndpoint)}?active=true`,
      modelRenderer: nameRenderer,
    },
    mm_size: {
      api_url: `${apiUrl(sizeEndpoint)}?active=true`,
      modelRenderer: nameRenderer,
    },
    color: {
      api_url: `${apiUrl(colorEndpoint)}?active=true`,
      modelRenderer: nameRenderer,
    },
    cut: {
      api_url: `${apiUrl(cutEndpoint)}?active=true`,
      modelRenderer: nameRenderer,
    },
    quality: {
      api_url: `${apiUrl(qualityEndpoint)}?active=true`,
      modelRenderer: nameRenderer,
    },
    setting: {
      api_url: `${apiUrl(ApiEndpoints.master_setting)}?active=true`,
      modelRenderer: nameRenderer,
    },
    stone_place: {
      api_url: `${apiUrl(ApiEndpoints.stone_place)}?active=true`,
      modelRenderer: nameRenderer,
    },
    pointer: {},
    sieve_size: {},
    pcs: {},
    cts: {},
    default_rate: {},
    pc: {},
    rate: {},
    amount: {},
    labour_rate: {},
    labour_amount: {},
    active: {},
  };
}

/** Diamond tab line fields — one row per diamond entry on the cost card. */
export function costCardDiamondLineFields(costCardId: number): ApiFormFieldSet {
  return {
    cost_card: { hidden: true, value: costCardId },
    ...costCardStoneLineFields(
      ApiEndpoints.diamond_stone_list,
      ApiEndpoints.diamond_shape_list,
      ApiEndpoints.diamond_size_list,
      ApiEndpoints.diamond_color_list,
      ApiEndpoints.diamond_cut_list,
      ApiEndpoints.diamond_quality_list,
    ),
  };
}

/** Color Stone tab line fields — one row per color stone entry on the cost card. */
export function costCardColorStoneLineFields(
  costCardId: number,
): ApiFormFieldSet {
  return {
    cost_card: { hidden: true, value: costCardId },
    ...costCardStoneLineFields(
      ApiEndpoints.color_stone_type_list,
      ApiEndpoints.color_stone_shape_list,
      ApiEndpoints.color_stone_size_list,
      ApiEndpoints.color_stone_color_list,
      ApiEndpoints.color_stone_cut_list,
      ApiEndpoints.color_stone_quality_list,
    ),
  };
}

/** Finish Type tab line fields — one row per finish applied to the cost card. */
export function costCardFinishLineFields(costCardId: number): ApiFormFieldSet {
  return {
    cost_card: { hidden: true, value: costCardId },
    finish_type: {
      api_url: `${apiUrl(ApiEndpoints.finish_type)}?active=true`,
      modelRenderer: (arg: any) => {
        const instance = arg?.instance ?? arg;
        return instance?.name ?? "";
      },
    },
    rate: {},
    active: {},
  };
}

export function DiamondStoneFields(): ApiFormFieldSet {
  return {
    name: {},
    description: {},
    active: {},
  };
}

export function diamondCutFields(): ApiFormFieldSet {
  return {
    name: {},
    description: {},
    active: {},
  };
}

export function diamondShapeFields(): ApiFormFieldSet {
  return {
    name: {},
    description: {},
    active: {},
  };
}

export function diamondColorFields(): ApiFormFieldSet {
  return {
    name: {},
    description: {},
    active: {},
  };
}

export function diamondSizeFields(): ApiFormFieldSet {
  return {
    name: {},
    mm_size: {},
    sieve_size: {},
    description: {},
    active: {},
  };
}

export function diamondQualityFields(): ApiFormFieldSet {
  return {
    name: {},
    description: {},
    active: {},
  };
}

export function diamondRateFields(): ApiFormFieldSet {
  return {
    shape: {
      api_url: `${apiUrl(ApiEndpoints.diamond_shape_list)}?active=true`,
      modelRenderer: (arg: any) => {
        const instance = arg?.instance ?? arg;
        return instance?.name ?? (instance?.name ? `#${instance.name}` : "");
      },
    },
    mm_size: {
      api_url: `${apiUrl(ApiEndpoints.diamond_size_list)}?active=true`,
      modelRenderer: (arg: any) => {
        const instance = arg?.instance ?? arg;
        return instance?.name ?? (instance?.name ? `#${instance.name}` : "");
      },
    },
    stone: {
      api_url: `${apiUrl(ApiEndpoints.diamond_stone_list)}?active=true`,
      modelRenderer: (arg: any) => {
        const instance = arg?.instance ?? arg;
        return instance?.name ?? (instance?.name ? `#${instance.name}` : "");
      },
    },
    color: {
      api_url: `${apiUrl(ApiEndpoints.diamond_color_list)}?active=true`,
      modelRenderer: (arg: any) => {
        const instance = arg?.instance ?? arg;
        return instance?.name ?? (instance?.name ? `#${instance.name}` : "");
      },
    },
    cut: {
      api_url: `${apiUrl(ApiEndpoints.diamond_cut_list)}?active=true`,
      modelRenderer: (arg: any) => {
        const instance = arg?.instance ?? arg;
        return instance?.name ?? (instance?.name ? `#${instance.name}` : "");
      },
    },
    quality: {
      api_url: `${apiUrl(ApiEndpoints.diamond_quality_list)}?active=true`,
      modelRenderer: (arg: any) => {
        const instance = arg?.instance ?? arg;
        return instance?.name ?? (instance?.name ? `#${instance.name}` : "");
      },
    },
    pointer: {},
    rate: {},
    pc: {
      default: "C",
    },
    customers: {
      field_type: "related field",
      model: ModelType.company,
      multiple: true,
      api_url: apiUrl(ApiEndpoints.company_list),
      filters: { is_customer: true },
      disableWhen: (values: any) => !!values?.all_customers,
      modelRenderer: (arg: any) => {
        const instance = arg?.instance ?? arg;
        return instance?.code ?? "";
      },
    },
    all_customers: {},
    active: {},
  };
}

export function useCustomStateFields(): ApiFormFieldSet {
  // Status codes
  const statusCodes = useGlobalStatusState();

  // Selected base status class
  const [statusClass, setStatusClass] = useState<string>("");

  // Construct a list of status options based on the selected status class
  const statusOptions: any[] = useMemo(() => {
    const options: any[] = [];

    const valuesList = Object.values(statusCodes.status ?? {}).find(
      (value: StatusCodeListInterface) => value.status_class === statusClass,
    );

    Object.values(valuesList?.values ?? {}).forEach(
      (value: StatusCodeInterface) => {
        options.push({
          value: value.key,
          display_name: value.label,
        });
      },
    );

    return options;
  }, [statusCodes, statusClass]);

  return useMemo(() => {
    return {
      reference_status: {
        onValueChange(value) {
          setStatusClass(value);
        },
      },
      logical_key: {
        field_type: "choice",
        choices: statusOptions,
      },
      key: {},
      name: {},
      label: {},
      color: {},
      model: {},
    };
  }, [statusOptions]);
}

export function customUnitsFields(): ApiFormFieldSet {
  return {
    name: {},
    definition: {},
    symbol: {},
  };
}

export function extraLineItemFields(): ApiFormFieldSet {
  return {
    order: {
      hidden: true,
    },
    line: {},
    reference: {},
    description: {},
    quantity: {},
    price: {},
    price_currency: {},
    project_code: ProjectCodeField(),
    notes: {},
    link: {},
  };
}

export function useParameterTemplateFields(): ApiFormFieldSet {
  return useMemo(() => {
    return {
      name: {},
      description: {},
      units: {},
      model_type: {},
      choices: {},
      checkbox: {},
      selectionlist: {
        filters: {
          active: true,
        },
      },
      enabled: {},
    };
  }, []);
}

/**
 * Shared hook for the dynamic "value" field on parameter forms.
 *
 * When the user selects a parameter template, the field type for the
 * corresponding value input (data / default_value) must change to match the
 * template's data type (boolean, choice, related-field selection list, or
 * plain string).  This hook encapsulates that state so it can be reused
 * across the "Add Parameter" and "Add Category Parameter" forms.
 *
 * @param resetDep - When this value changes all internal state is reset to
 *   defaults.  Pass a stringified key derived from the form's context (e.g.
 *   `${modelType}-${modelId}`) so the field resets when the context switches.
 */
export function useDynamicParameterValueField(resetDep?: any): {
  onTemplateValueChange: (value: any, record: any) => void;
  valueFieldConfig: ApiFormFieldType;
  reset: () => void;
} {
  const api = useApi();

  const [selectionListId, setSelectionListId] = useState<number | null>(null);
  const [choices, setChoices] = useState<any[]>([]);
  const [fieldType, setFieldType] = useState<
    "string" | "boolean" | "choice" | "related field"
  >("string");
  const [data, setData] = useState<string>("");

  const reset = useCallback(() => {
    setSelectionListId(null);
    setFieldType("string");
    setChoices([]);
    setData("");
  }, []);

  useEffect(() => {
    reset();
  }, [resetDep, reset]);

  const fetchSelectionEntry = useCallback(
    (value: any) => {
      if (!value || !selectionListId) {
        return null;
      }

      return api
        .get(apiUrl(ApiEndpoints.selectionentry_list, selectionListId), {
          params: { value: value },
        })
        .then((response) => {
          if (response.data && response.data.length == 1) {
            return response.data[0];
          } else {
            return null;
          }
        });
    },
    [selectionListId],
  );

  const onTemplateValueChange = useCallback(
    (value: any, record: any) => {
      setSelectionListId(record?.selectionlist || null);
      setData("");

      if (record?.checkbox) {
        setChoices([]);
        setFieldType("boolean");
        setData("false");
      } else if (record?.choices) {
        const _choices: string[] = record.choices.split(",");

        if (_choices.length > 0) {
          setChoices(
            _choices.map((choice) => ({
              display_name: choice.trim(),
              value: choice.trim(),
            })),
          );
          setFieldType("choice");
        } else {
          setChoices([]);
          setFieldType("string");
          setData("");
        }
      } else if (record?.selectionlist) {
        setFieldType("related field");
        setData("");
      } else {
        setFieldType("string");
        setData("");
      }
    },
    [setFieldType, setData, setChoices],
  );

  const valueFieldConfig: ApiFormFieldType = useMemo(
    () => ({
      value: data,
      onValueChange: (value: any, record: any) => {
        if (fieldType === "related field" && selectionListId) {
          // For related fields, store the primary key value (not the string representation)
          setData(record?.value ?? value);
        } else {
          setData(value);
        }
      },
      field_type: fieldType,
      choices: fieldType === "choice" ? choices : undefined,
      default: fieldType === "boolean" ? false : undefined,
      pk_field:
        fieldType === "related field" && selectionListId ? "value" : undefined,
      model:
        fieldType === "related field" && selectionListId
          ? ModelType.selectionentry
          : undefined,
      api_url:
        fieldType === "related field" && selectionListId
          ? apiUrl(ApiEndpoints.selectionentry_list, selectionListId)
          : undefined,
      filters: fieldType === "related field" ? { active: true } : undefined,
      adjustValue: (value: any) => {
        let v: string = value.toString().trim();

        if (fieldType === "boolean") {
          if (v.toLowerCase() !== "true") {
            v = "false";
          }
        }

        return v;
      },
      singleFetchFunction: fetchSelectionEntry,
    }),
    [data, fieldType, choices, selectionListId, fetchSelectionEntry],
  );

  return { onTemplateValueChange, valueFieldConfig, reset };
}

export function useParameterFields({
  modelType,
  modelId,
}: {
  modelType: ModelType;
  modelId: number;
}): ApiFormFieldSet {
  const user = useUserState.getState();
  const templateCreateFields = useParameterTemplateFields();

  const resetKey = useMemo(
    () => `${modelType}-${modelId}`,
    [modelType, modelId],
  );
  const { onTemplateValueChange, valueFieldConfig } =
    useDynamicParameterValueField(resetKey);

  return useMemo(() => {
    return {
      model_type: {
        hidden: true,
        value: modelType,
      },
      model_id: {
        hidden: true,
        value: modelId,
      },
      template: {
        filters: {
          for_model: modelType,
          enabled: true,
        },
        onValueChange: onTemplateValueChange,
        addCreateFields: user.isStaff() ? templateCreateFields : undefined,
      },
      data: valueFieldConfig,
      note: {},
    };
  }, [
    modelType,
    modelId,
    onTemplateValueChange,
    valueFieldConfig,
    templateCreateFields,
    user,
  ]);
}

export function selectionListFields(): ApiFormFieldSet {
  return {
    name: {},
    description: {},
    active: {},
    source_plugin: {},
    source_string: {},
  };
}

export function selectionEntryFields(): ApiFormFieldSet {
  return {
    value: {},
    label: {},
    description: {},
    active: {},
  };
}
