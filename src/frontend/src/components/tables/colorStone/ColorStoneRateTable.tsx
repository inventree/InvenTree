import { t } from "@lingui/core/macro";
import { useCallback, useMemo, useState } from "react";

import { AddItemButton } from "@lib/components/AddItemButton";
import {
  type RowAction,
  RowDeleteAction,
  RowEditAction,
} from "@lib/components/RowActions";
import { ApiEndpoints } from "@lib/enums/ApiEndpoints";
import { UserRoles } from "@lib/enums/Roles";
import { apiUrl } from "@lib/functions/Api";
import useTable from "@lib/hooks/UseTable";
import type { TableFilter } from "@lib/index";
import type { TableColumn } from "@lib/types/Tables";
import { BooleanColumn, DescriptionColumn } from "../ColumnRenderers";
import { InvenTreeTable } from "../InvenTreeTable";
import { colorStoneRateFields } from "../../forms/CommonForms";
import {
  useCreateApiFormModal,
  useDeleteApiFormModal,
  useEditApiFormModal,
} from "../../../hooks/UseForm";
import { useApi } from "@context/ApiContext";
import { useUserState } from "@store/UserState";
import { useQuery, useQueryClient } from "@tanstack/react-query";

const STONE_RATE_LOOKUP_QUERY_KEYS = [
  ["stone-shape-lookup"],
  ["stone-size-lookup"],
  ["stone-stone-lookup"],
  ["stone-color-lookup"],
  ["stone-cut-lookup"],
  ["stone-quality-lookup"],
];
/**
 * Table for displaying, creating, editing and deleting Metal Type records
 */
export default function ColorStoneRateTable() {
  const table = useTable("stone-rate");

  const api = useApi();
  const user = useUserState();
  const queryClient = useQueryClient();

  const refreshLookupTables = useCallback(() => {
    STONE_RATE_LOOKUP_QUERY_KEYS.forEach((queryKey) => {
      queryClient.invalidateQueries({ queryKey });
    });
  }, [queryClient]);

  // Stone Shape
  const stoneShapeQuery = useQuery({
    queryKey: ["stone-shape-lookup"],
    queryFn: () =>
      api
        .get(apiUrl(ApiEndpoints.color_stone_shape_list), {
          params: { limit: 1000 },
        })
        .then((response) => response.data?.results ?? response.data ?? []),
    staleTime: 5 * 60 * 1000,
    refetchOnMount: "always",
  });
  const stoneShapeNameByPk = useMemo(() => {
    const map: Record<number, string> = {};
    (stoneShapeQuery.data ?? []).forEach((stoneShape: any) => {
      map[stoneShape.pk] = stoneShape.name;
    });
    return map;
  }, [stoneShapeQuery.data]);

  // Stone Size
  const stoneSizeQuery = useQuery({
    queryKey: ["stone-size-lookup"],
    queryFn: () =>
      api
        .get(apiUrl(ApiEndpoints.color_stone_size_list), {
          params: { limit: 1000 },
        })
        .then((response) => response.data?.results ?? response.data ?? []),
    staleTime: 5 * 60 * 1000,
    refetchOnMount: "always",
  });
  const stoneSizeNameByPk = useMemo(() => {
    const map: Record<number, string> = {};

    (stoneSizeQuery.data ?? []).forEach((stoneSize: any) => {
      map[stoneSize.pk] = stoneSize.mm_size;
    });

    return map;
  }, [stoneSizeQuery.data]);

  // Stone Stone
  const stoneStoneQuery = useQuery({
    queryKey: ["stone-stone-lookup"],
    queryFn: () =>
      api
        .get(apiUrl(ApiEndpoints.color_stone_type_list), {
          params: { limit: 1000 },
        })
        .then((response) => response.data?.results ?? response.data ?? []),
    staleTime: 5 * 60 * 1000,
    refetchOnMount: "always",
  });
  const stoneStoneNameByPk = useMemo(() => {
    const map: Record<number, string> = {};

    (stoneStoneQuery.data ?? []).forEach((stoneStone: any) => {
      map[stoneStone.pk] = stoneStone.name;
    });

    return map;
  }, [stoneStoneQuery.data]);

  // Stone Color
  const stoneColorQuery = useQuery({
    queryKey: ["stone-color-lookup"],
    queryFn: () =>
      api
        .get(apiUrl(ApiEndpoints.color_stone_color_list), {
          params: { limit: 1000 },
        })
        .then((response) => response.data?.results ?? response.data ?? []),
    staleTime: 5 * 60 * 1000,
    refetchOnMount: "always",
  });
  const stoneColorNameByPk = useMemo(() => {
    const map: Record<number, string> = {};

    (stoneColorQuery.data ?? []).forEach((stoneColor: any) => {
      map[stoneColor.pk] = stoneColor.name;
    });

    return map;
  }, [stoneColorQuery.data]);

  // Stone Cut
  const stoneCutQuery = useQuery({
    queryKey: ["stone-cut-lookup"],
    queryFn: () =>
      api
        .get(apiUrl(ApiEndpoints.color_stone_cut_list), {
          params: { limit: 1000 },
        })
        .then((response) => response.data?.results ?? response.data ?? []),
    staleTime: 5 * 60 * 1000,
    refetchOnMount: "always",
  });
  const stoneCutNameByPk = useMemo(() => {
    const map: Record<number, string> = {};

    (stoneCutQuery.data ?? []).forEach((stoneCut: any) => {
      map[stoneCut.pk] = stoneCut.name;
    });

    return map;
  }, [stoneCutQuery.data]);

  // Stone Quality
  const stoneQualityQuery = useQuery({
    queryKey: ["stone-quality-lookup"],
    queryFn: () =>
      api
        .get(apiUrl(ApiEndpoints.color_stone_quality_list), {
          params: { limit: 1000 },
        })
        .then((response) => response.data?.results ?? response.data ?? []),
    staleTime: 5 * 60 * 1000,
    refetchOnMount: "always",
  });
  const stoneQualityNameByPk = useMemo(() => {
    const map: Record<number, string> = {};

    (stoneQualityQuery.data ?? []).forEach((stoneQuality: any) => {
      map[stoneQuality.pk] = stoneQuality.name;
    });

    return map;
  }, [stoneQualityQuery.data]);

  // --- Table columns -------------------------------------------------
  const columns: TableColumn[] = useMemo(() => {
    return [
      {
        accessor: "shape",
        sortable: true,
        switchable: false,
        render: (record: any) =>
          stoneShapeNameByPk[record.shape] ?? record.shape,
      },
      {
        accessor: "mm_size",
        title: t`Size in mm`,
        sortable: true,
        switchable: false,
        render: (record: any) =>
          stoneSizeNameByPk[record.mm_size] ?? record.mm_size,
      },
      {
        accessor: "stone",
        sortable: true,
        switchable: false,
        render: (record: any) =>
          stoneStoneNameByPk[record.stone] ?? record.stone,
      },
      {
        accessor: "color",
        sortable: true,
        switchable: false,
        render: (record: any) =>
          stoneColorNameByPk[record.color] ?? record.color,
      },
      {
        accessor: "cut",
        sortable: true,
        switchable: false,
        render: (record: any) => stoneCutNameByPk[record.cut] ?? record.cut,
      },
      {
        accessor: "quality",
        sortable: true,
        switchable: false,
        render: (record: any) =>
          stoneQualityNameByPk[record.quality] ?? record.quality,
      },
      {
        accessor: "pointer",
        sortable: true,
        switchable: false,
      },
      {
        accessor: "rate",
        sortable: true,
        switchable: false,
      },
      {
        accessor: "pc",
        sortable: true,
        switchable: false,
      },
      {
        accessor: "customers",
        title: t`Customers`,
        sortable: false,
        switchable: false,
        render: (record: any) => {
          if (record.all_customers) {
            return t`All Customers`;
          }
          const codes = (record.customers_detail ?? [])
            .map((customer: any) => customer.code)
            .filter(Boolean);
          return codes.length > 0 ? codes.join(", ") : "-";
        },
      },
      BooleanColumn({
        accessor: "active",
      }),
      {
        accessor: "created_at",
        title: t`Created`,
        sortable: true,
        switchable: true,
      },
      {
        accessor: "updated_at",
        title: t`Updated`,
        sortable: true,
        switchable: true,
      },
    ];
  }, [
    stoneShapeNameByPk,
    stoneSizeNameByPk,
    stoneStoneNameByPk,
    stoneColorNameByPk,
    stoneCutNameByPk,
    stoneQualityNameByPk,
  ]);

  // --- Create modal ----------------------------------------------------
  const newStoneRate = useCreateApiFormModal({
    url: ApiEndpoints.color_stone_rate_list,
    title: t`Add Stone Rate`,
    fields: colorStoneRateFields(),
    table: table,
    onFormSuccess: () => {
      refreshLookupTables();
    },
  });

  // --- Edit / Delete modals --------------------------------------------
  const [selectedStoneRate, setSelectedStoneRate] = useState<
    number | undefined
  >(undefined);

  const editStoneRate = useEditApiFormModal({
    url: ApiEndpoints.color_stone_rate_list,
    pk: selectedStoneRate,
    title: t`Edit Stone Rate`,
    fields: colorStoneRateFields(),
    table: table,
    onFormSuccess: () => {
      refreshLookupTables();
    },
  });

  const deleteStoneRate = useDeleteApiFormModal({
    url: ApiEndpoints.color_stone_rate_list,
    pk: selectedStoneRate,
    title: t`Delete Stone Rate`,
    table: table,
  });

  // --- Row actions (edit / delete) -------------------------------------
  const rowActions = useCallback(
    (record: any): RowAction[] => {
      return [
        RowEditAction({
          hidden: !user.hasChangeRole(UserRoles.part),
          onClick: () => {
            setSelectedStoneRate(record.pk);
            editStoneRate.open();
          },
        }),
        RowDeleteAction({
          hidden: !user.hasDeleteRole(UserRoles.part),
          onClick: () => {
            setSelectedStoneRate(record.pk);
            deleteStoneRate.open();
          },
        }),
      ];
    },
    [user],
  );

  // --- Table-level filters ----------------------------------------------
  const tableFilters: TableFilter[] = useMemo(() => {
    return [
      {
        name: "active",
        label: t`Active`,
        description: t`Show active stone qualities`,
        type: "boolean",
      },
    ];
  }, []);

  // --- Toolbar actions (Add button) --------------------------------------
  const tableActions = useMemo(() => {
    return [
      <AddItemButton
        key="add-stone-rate"
        onClick={() => newStoneRate.open()}
        tooltip={t`Add Stone Rate`}
        hidden={!user.hasAddRole(UserRoles.part)}
      />,
    ];
  }, [user]);

  return (
    <>
      {newStoneRate.modal}
      {editStoneRate.modal}
      {deleteStoneRate.modal}
      <InvenTreeTable
        url={apiUrl(ApiEndpoints.color_stone_rate_list)}
        tableState={table}
        columns={columns}
        props={{
          rowActions: rowActions,
          tableActions: tableActions,
          tableFilters: tableFilters,
          enableDownload: true,
        }}
      />
    </>
  );
}
