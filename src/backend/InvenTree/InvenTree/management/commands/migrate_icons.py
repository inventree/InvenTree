"""Custom management command to migrate the old FontAwesome icons."""

import json

from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.db import models

from common.icons import validate_icon
from part.models import PartCategory
from stock.models import StockLocation, StockLocationType


class Command(BaseCommand):
    """Generate an icon map from the FontAwesome library to the new icon library."""

    help = """Helper command to migrate the old FontAwesome icons to the new icon library."""

    def add_arguments(self, parser):
        """Add the arguments."""
        parser.add_argument(
            '--output-file',
            type=str,
            help='Path to file to write generated icon map to',
        )
        parser.add_argument(
            '--input-file', type=str, help='Path to file to read icon map from'
        )
        parser.add_argument(
            '--include-items',
            default=False,
            action='store_true',
            help='Include referenced inventree items in the output icon map (optional)',
        )
        parser.add_argument(
            '--import-now',
            default=False,
            action='store_true',
            help='CAUTION: If this flag is set, the icon map will be imported and the database will be touched',
        )

    def handle(self, *args, **kwargs):
        """Generate an icon map from the FontAwesome library to the new icon library."""
        # Check for invalid combinations of arguments
        if kwargs['output_file'] and kwargs['input_file']:
            raise CommandError('Cannot specify both --input-file and --output-file')

        if not kwargs['output_file'] and not kwargs['input_file']:
            raise CommandError('Must specify either --input-file or --output-file')

        if kwargs['include_items'] and not kwargs['output_file']:
            raise CommandError(
                '--include-items can only be used with an --output-file specified'
            )

        if kwargs['output_file'] and kwargs['import_now']:
            raise CommandError(
                '--import-now can only be used with an --input-file specified'
            )

        ICON_MODELS = [
            (StockLocation, 'custom_icon'),
            (StockLocationType, 'icon'),
            (PartCategory, '_icon'),
        ]

        def get_model_items_with_icons(model: models.Model, icon_field: str):
            """Return a list of models with icon fields."""
            return model.objects.exclude(**{f'{icon_field}__isnull': True}).exclude(**{
                f'{icon_field}__exact': ''
            })

        # Generate output icon map file
        if kwargs['output_file']:
            icons = {}

            for model, icon_name in ICON_MODELS:
                self.stdout.write(
                    f'Processing model {model.__name__} with icon field {icon_name}'
                )

                items = get_model_items_with_icons(model, icon_name)

                for item in items:
                    icon = getattr(item, icon_name)

                    try:
                        validate_icon(icon)
                        continue  # Skip if the icon is already valid
                    except ValidationError:
                        pass

                    if icon not in icons:
                        icons[icon] = {
                            **({'items': []} if kwargs['include_items'] else {}),
                            'new_icon': '',
                        }

                    if kwargs['include_items']:
                        icons[icon]['items'].append({
                            'model': model.__name__.lower(),
                            'id': item.id,  # type: ignore
                        })

            self.stdout.write(f'Writing icon map for {len(icons.keys())} icons')
            with open(kwargs['output_file'], 'w', encoding='utf-8') as f:
                json.dump(icons, f, indent=2)

            self.stdout.write(f'Icon map written to {kwargs["output_file"]}')

        # Import icon map file
        if kwargs['input_file']:
            with open(kwargs['input_file'], encoding='utf-8') as f:
                icons = json.load(f)

            self.stdout.write(f'Loaded icon map for {len(icons.keys())} icons')

            self.stdout.write('Verifying icon map')
            has_errors = False

            # Verify that all new icons are valid icons
            for old_icon, data in icons.items():
                try:
                    validate_icon(data.get('new_icon', ''))
                except ValidationError:
                    self.stdout.write(
                        f'[ERR] Invalid icon: "{old_icon}" -> "{data.get("new_icon", "")}'
                    )
                    has_errors = True

            # Verify that all required items are provided in the icon map
            for model, icon_name in ICON_MODELS:
                self.stdout.write(
                    f'Processing model {model.__name__} with icon field {icon_name}'
                )
                items = get_model_items_with_icons(model, icon_name)

                for item in items:
                    icon = getattr(item, icon_name)

                    try:
                        validate_icon(icon)
                        continue  # Skip if the icon is already valid
                    except ValidationError:
                        pass

                    if icon not in icons:
                        self.stdout.write(
                            f'  [ERR] Icon "{icon}" not found in icon map'
                        )
                        has_errors = True

            # If there are errors, stop here
            if has_errors:
                self.stdout.write(
                    '[ERR] Icon map has errors, please fix them before continuing with importing'
                )
                return

            # Import the icon map into the database if the flag is set
            if kwargs['import_now']:
                self.stdout.write('Start importing icons and updating database...')
                cnt = 0

                for model, icon_name in ICON_MODELS:
                    self.stdout.write(
                        f'Processing model {model.__name__} with icon field {icon_name}'
                    )
                    items = get_model_items_with_icons(model, icon_name)

                    for item in items:
                        icon = getattr(item, icon_name)

                        try:
                            validate_icon(icon)
                            continue  # Skip if the icon is already valid
                        except ValidationError:
                            pass

                        setattr(item, icon_name, icons[icon]['new_icon'])
                        cnt += 1
                        item.save()

                self.stdout.write(
                    f'Icon map successfully imported - changed {cnt} items'
                )
                self.stdout.write('Icons are now migrated')
            else:
                self.stdout.write('Icon map is valid and ready to be imported')
                self.stdout.write(
                    'Run the command with --import-now to import the icon map and update the database'
                )
