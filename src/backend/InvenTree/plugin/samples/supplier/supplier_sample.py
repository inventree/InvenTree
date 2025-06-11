"""Sample supplier plugin."""

from plugin.base.supplier.mixins import SupplierMixin
from plugin.plugin import InvenTreePlugin


class SampleSupplierPlugin(SupplierMixin, InvenTreePlugin):
    """Example plugin to integrate with a dummy supplier."""

    NAME = 'SampleSupplierPlugin'
    SLUG = 'samplesupplier'
    TITLE = 'My sample supplier plugin'

    VERSION = '0.0.1'

    SUPPLIER_NAME = 'Sample Supplier'

    def get_search_results(self, term: str) -> list[SupplierMixin.SearchResult]:
        """Return a list of search results based on the search term."""
        return [
            SupplierMixin.SearchResult(
                sku=f'SAMPLE-001-{idx}',
                name=f'Sample Part 1 T: {term}',
                exact=True,
                description='This is a sample part for demonstration purposes.',
                price='10.00€',
                link='https://example.com/sample-part-1',
                image_url=r'https://cdn-reichelt.de/bilder/web/artikel_ws/D330%2FEINHELL_3410310_01.jpg?type=Product&',
                id=f'sample-001-{idx}',
            )
            for idx in range(20)
        ]
