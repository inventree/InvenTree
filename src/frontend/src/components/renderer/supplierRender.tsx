import { ThumbnailHoverCard } from '../items/Thumbnail';

export function supplierRender(record: any) {
  const supplier = record.supplier_detail;
  return (
    supplier && (
      <ThumbnailHoverCard
        src={supplier.thumbnail || supplier.image}
        text={supplier.name}
        link={supplier.url}
      />
    )
  );
}
