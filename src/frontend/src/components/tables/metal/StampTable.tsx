import { t } from "@lingui/core/macro";
import { useCallback, useEffect, useMemo, useState } from "react";

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
import { stampFields } from "../../forms/CommonForms";
import {
  useCreateApiFormModal,
  useDeleteApiFormModal,
  useEditApiFormModal,
} from "../../../hooks/UseForm";
import { useUserState } from "@store/UserState";
import { Thumbnail } from "@components/shared/images/Thumbnail";
import { Button, Group } from "@mantine/core";

export default function StampTable() {
  const table = useTable("stamp");
  const user = useUserState();

  // --- Table columns -------------------------------------------------
  const columns: TableColumn[] = useMemo(() => {
    return [
      {
        accessor: "image",
        title: t`Image`,
        sortable: false,
        switchable: true,
        render: (record: any) => (
          <Thumbnail src={record.image} alt={record.name} size={24} hover />
        ),
      },
      {
        accessor: "name",
        sortable: true,
        switchable: false,
      },
      DescriptionColumn({}),
      // {
      //   accessor: "customers",
      //   title: t`Customers`,
      //   sortable: false,
      //   switchable: false,
      //   render: (record: any) => {
      //     if (record.all_customers) {
      //       return t`All Customers`;
      //     }
      //     const codes = (record.customers_detail ?? [])
      //       .map((customer: any) => customer.code)
      //       .filter(Boolean);
      //     return codes.length > 0 ? codes.join(", ") : "-";
      //   },
      // },
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
  }, []);

  // --- Create modal ----------------------------------------------------

  const [createPreviewImage, setCreatePreviewImage] = useState<
    string | undefined
  >(undefined);

  const handleCreateImageChange = useCallback((file: File | null) => {
    setCreatePreviewImage((prev) => {
      if (prev) URL.revokeObjectURL(prev); // free the old blob url
      return file ? URL.createObjectURL(file) : undefined;
    });
  }, []);
  const newStamp = useCreateApiFormModal({
    url: ApiEndpoints.master_stamp,
    title: t`Add Stamp`,
    fields: stampFields(true, handleCreateImageChange), // allow to create image hence true
    table: table,
    preFormContent: (
      <Group justify="center" mb="sm">
        <Thumbnail src={createPreviewImage} alt={t`New Stamp`} size={60} />
      </Group>
    ),
    onClose: () => {
      setCreatePreviewImage((prev) => {
        if (prev) URL.revokeObjectURL(prev);
        return undefined;
      });
    },
  });

  // --- Edit / Delete modals --------------------------------------------
  const [selectedStamp, setSelectedStamp] = useState<any | undefined>(
    undefined,
  );
  const [changeImage, setChangeImage] = useState(false);
  const [previewImage, setPreviewImage] = useState<string | undefined>(
    undefined,
  );

  const handleImageChange = useCallback((file: File | null) => {
    setPreviewImage((prev) => {
      if (prev) URL.revokeObjectURL(prev);
      return file ? URL.createObjectURL(file) : undefined;
    });
  }, []);

  const editStamp = useEditApiFormModal({
    url: ApiEndpoints.master_stamp,
    pk: selectedStamp?.pk,
    title: t`Edit Stamp`,
    fields: stampFields(changeImage, handleImageChange),
    table: table,
    preFormContent: (
      <Group justify="space-between" mb="sm">
        <Thumbnail
          src={previewImage ?? selectedStamp?.image}
          alt={selectedStamp?.name}
          size={60}
        />
        {!changeImage && (
          <Button
            type="button"
            variant="subtle"
            size="xs"
            onClick={() => setChangeImage(true)}
          >
            {t`Change Image`}
          </Button>
        )}
      </Group>
    ),
    onClose: () => {
      setChangeImage(false);
      setPreviewImage((prev) => {
        if (prev) URL.revokeObjectURL(prev);
        return undefined;
      });
    },
  });

  const deleteStamp = useDeleteApiFormModal({
    url: ApiEndpoints.master_stamp,
    pk: selectedStamp,
    title: t`Delete Stamp`,
    table: table,
  });

  // --- Row actions (edit / delete) -------------------------------------
  const rowActions = useCallback(
    (record: any): RowAction[] => {
      return [
        RowEditAction({
          hidden: !user.hasChangeRole(UserRoles.part),
          onClick: () => {
            setChangeImage(false);
            setPreviewImage(undefined);
            setSelectedStamp(record);
            editStamp.open();
          },
        }),
        RowDeleteAction({
          hidden: !user.hasDeleteRole(UserRoles.part),
          onClick: () => {
            setSelectedStamp(record.pk);
            deleteStamp.open();
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
        description: t`Show active stamp`,
        type: "boolean",
      },
    ];
  }, []);

  // --- Toolbar actions (Add button) --------------------------------------
  const tableActions = useMemo(() => {
    return [
      <AddItemButton
        key="add-stamp"
        onClick={() => newStamp.open()}
        tooltip={t`Add Stamp`}
        hidden={!user.hasAddRole(UserRoles.part)}
      />,
    ];
  }, [user]);

  return (
    <>
      {newStamp.modal}
      {editStamp.modal}
      {deleteStamp.modal}
      <InvenTreeTable
        url={apiUrl(ApiEndpoints.master_stamp)}
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
