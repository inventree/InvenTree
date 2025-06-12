"""Sample supplier plugin."""

from company.models import Company, ManufacturerPart, SupplierPart, SupplierPriceBreak
from part.models import Part
from plugin.base.supplier.mixins import SupplierMixin
from plugin.plugin import InvenTreePlugin


class SampleSupplierPlugin(SupplierMixin, InvenTreePlugin):
    """Example plugin to integrate with a dummy supplier."""

    NAME = 'SampleSupplierPlugin'
    SLUG = 'samplesupplier'
    TITLE = 'My sample supplier plugin'

    VERSION = '0.0.1'

    SUPPLIER_NAME = 'Sample Supplier'

    def __init__(self):
        """Initialize the sample supplier plugin."""
        super().__init__()

        self.sample_data = []
        for material in ['Steel', 'Aluminium', 'Brass']:
            for size in ['M1', 'M2', 'M3', 'M4', 'M5']:
                for length in range(5, 30, 5):
                    self.sample_data.append({
                        'material': material,
                        'thread': size,
                        'length': length,
                        'sku': f'BOLT-{material}-{size}-{length}',
                        'name': f'Bolt {size}x{length}mm {material}',
                        'description': f'This is a sample part description demonstration purposes for the {size}x{length} {material} bolt.',
                        'price': {
                            1: [1.0, 'EUR'],
                            10: [0.9, 'EUR'],
                            100: [0.8, 'EUR'],
                            5000: [0.5, 'EUR'],
                        },
                        'link': f'https://example.com/sample-part-{size}-{length}-{material}',
                        'image_url': r'https://demo.inventree.org/media/part_images/flat-head.png',
                        'brand': 'Bolt Manufacturer',
                    })

    def get_search_results(self, term: str) -> list[SupplierMixin.SearchResult]:
        """Return a list of search results based on the search term."""
        return [
            SupplierMixin.SearchResult(
                sku=p['sku'],
                name=p['name'],
                description=p['description'],
                exact=p['sku'] == term,
                price=f'{p["price"][1][0]:.2f}€',
                link=p['link'],
                image_url=p['image_url'],
                existing_part=getattr(
                    SupplierPart.objects.filter(SKU=p['sku']).first(), 'part', None
                ),
            )
            for p in self.sample_data
            if all(t.lower() in p['name'].lower() for t in term.split())
        ]

    def get_import_data(self, part_id: str):
        """Return import data for a specific part ID."""
        for p in self.sample_data:
            if p['sku'] == part_id:
                p = p.copy()
                p['variants'] = [
                    x['sku']
                    for x in self.sample_data
                    if x['thread'] == p['thread'] and x['length'] == p['length']
                ]
                return p

        raise SupplierMixin.PartNotFoundError()

    def get_pricing_data(self, data) -> dict[int, tuple[float, str]]:
        """Return pricing data for the given part data."""
        return data['price']

    def get_parameters(self, data) -> list[SupplierMixin.ImportParameter]:
        """Return a list of parameters for the given part data."""
        return [
            SupplierMixin.ImportParameter(name='Thread', value=data['thread'][1:]),
            SupplierMixin.ImportParameter(name='Length', value=f'{data["length"]}mm'),
            SupplierMixin.ImportParameter(name='Material', value=data['material']),
            SupplierMixin.ImportParameter(name='Head', value='Flat Head'),
        ]

    def import_part(self, data, **kwargs) -> Part:
        """Import a part based on the provided data."""
        part, created = Part.objects.get_or_create(
            name__iexact=data['sku'],
            purchaseable=True,
            defaults={
                'name': data['name'],
                'description': data['description'],
                'link': data['link'],
                **kwargs,
            },
        )

        # If the part was created, set additional fields
        if created:
            if data['image_url']:
                file, fmt = self.download_image(data['image_url'])
                filename = f'part_{part.pk}_image.{fmt.lower()}'
                part.image.save(filename, file)

            # link other variants if they exist in our inventree database
            if len(data['variants']):
                # search for other parts that may already have a template part associated
                variant_parts = [
                    x.part
                    for x in SupplierPart.objects.filter(SKU__in=data['variants'])
                ]
                parent_part = self.get_template_part(
                    variant_parts,
                    {
                        # we cannot extract a real name for the root part, but we can try to guess a unique name
                        'name': data['sku'].replace(data['material'] + '-', ''),
                        'description': data['name'].replace(' ' + data['material'], ''),
                        'link': data['link'],
                        'image': part.image.name,
                        'is_template': True,
                        **kwargs,
                    },
                )
                part.variant_of = parent_part
                part.save()

        return part

    def import_manufacturer_part(self, data, **kwargs) -> ManufacturerPart:
        """Import a manufacturer part based on the provided data."""
        mft, _ = Company.objects.get_or_create(
            name__iexact=data['brand'],
            defaults={
                'is_manufacturer': True,
                'is_supplier': False,
                'name': data['brand'],
            },
        )

        mft_part, created = ManufacturerPart.objects.get_or_create(
            MPN=f'MAN-{data["sku"]}', manufacturer=mft, **kwargs
        )

        if created:
            # Attachments, notes, parameters and more can be added here
            pass

        return mft_part

    def import_supplier_part(self, data, **kwargs) -> SupplierPart:
        """Import a supplier part based on the provided data."""
        spp, _ = SupplierPart.objects.get_or_create(
            SKU=data['sku'],
            supplier=self.supplier,
            **kwargs,
            defaults={'link': data['link']},
        )

        SupplierPriceBreak.objects.filter(part=spp).delete()
        SupplierPriceBreak.objects.bulk_create([
            SupplierPriceBreak(
                part=spp, quantity=quantity, price=price, price_currency=currency
            )
            for quantity, (price, currency) in data['price'].items()
        ])

        return spp
