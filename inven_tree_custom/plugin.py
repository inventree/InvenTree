# inven_tree_custom/plugin.py
from django.urls import reverse_lazy, path, include
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.db import transaction, OperationalError, ProgrammingError

# Core InvenTree plugin imports
try:
    from plugin import InvenTreePlugin
    from plugin.registry import registry
except ImportError:
    print("Core InvenTree plugin components (InvenTreePlugin, registry) not found. Using placeholders.")
    class InvenTreePlugin: pass
    class Registry:
        def register(self, cls, **kwargs): pass
    registry = Registry()

# Attempt to import NavigationMixin
try:
    from plugin.mixins import NavigationMixin
except ImportError:
    NavigationMixin = object # Placeholder
    print("Note: NavigationMixin not found, navigation might not work as expected.")

# Signal and model imports (critical for functionality)
try:
    from stock.signals import stockitem_saved
    from stock.models import StockItem as StockItemModel # Alias for clarity
except ImportError:
    stockitem_saved = None
    StockItemModel = None
    print("WARNING: stock.signals.stockitem_saved or stock.models.StockItem not found. PN generation will fail.")

# Local imports
from .utils import generate_pn
from .dispatch import urls as dispatch_urls


class InvenTreeCustomPlugin(NavigationMixin, InvenTreePlugin):
    """
    Custom plugin for InvenTree to manage custom product numbers and dispatches.
    """

    NAME = "InvenTree Custom Logic"
    SLUG = "inventreecustom" 
    TITLE = "InvenTree Custom Logic & Dispatch" 
    VERSION = "0.3.0" # Updated VERSION for permissions feature
    AUTHOR = "AI Assistant"
    DESCRIPTION = "Provides custom product number generation, a dispatch management system, and role-based permissions."
    # WEBSITE = "..." # Optional

    NAVIGATION = [
        {
            'name': 'Dispatches',
            'link': 'plugin:inventreecustom:dispatch:dispatch_list', 
            'icon': 'fas fa-truck',
        },
        {
            'name': 'Stickers (Parts)',
            'link': 'part_list', 
            'icon': 'fas fa-tags',
        },
        {
            'name': 'Parameter Templates',
            'link': 'admin:common_parametertemplate_changelist',
            'icon': 'fas fa-cogs',
        },
    ]

    def __init__(self):
        super().__init__()
        self.setup_signals()
        try:
            self.setup_custom_permissions()
        except (OperationalError, ProgrammingError) as e:
            print(f"WARNING: Could not set up custom permissions for {self.NAME} due to DB issue: {e}. This might be normal during initial migrations.")

    @transaction.atomic
    def setup_custom_permissions(self):
        """
        Create custom groups and assign permissions for the dispatch models.
        """
        print(f"Setting up custom permissions for {self.NAME}...")

        # Define group names
        DISPATCH_GROUP_NAME = "Dispatch Team"
        PRODUCTION_GROUP_NAME = "Production Team" 

        # Create groups if they don't exist
        dispatch_team_group, created_dispatch_group = Group.objects.get_or_create(name=DISPATCH_GROUP_NAME)
        if created_dispatch_group:
            print(f"Created group: {DISPATCH_GROUP_NAME}")
        
        production_team_group, created_production_group = Group.objects.get_or_create(name=PRODUCTION_GROUP_NAME)
        if created_production_group:
            print(f"Created group: {PRODUCTION_GROUP_NAME}")

        # Assign permissions for Dispatch and DispatchItem models
        try:
            # Import models here to ensure apps are ready and to avoid circular dependency issues.
            from .dispatch.models import Dispatch, DispatchItem

            models_to_permission = [Dispatch, DispatchItem]
            permissions_for_dispatch_team = []
            permissions_for_production_team = []

            for model_cls in models_to_permission:
                # This inner try-except handles cases where ContentType for a specific model might not be ready
                try:
                    ct = ContentType.objects.get_for_model(model_cls)
                    model_permissions = Permission.objects.filter(content_type=ct)
                    
                    for perm in model_permissions:
                        permissions_for_dispatch_team.append(perm)
                        if perm.codename.startswith('view_'):
                            permissions_for_production_team.append(perm)
                except Exception as e_model:
                    print(f"Warning: Could not get ContentType or Permissions for model {model_cls.__name__}: {e_model}. This specific model's permissions might not be set.")
                    # Continue to the next model if one fails

            if permissions_for_dispatch_team:
                dispatch_team_group.permissions.add(*permissions_for_dispatch_team)
                print(f"Assigned {len(permissions_for_dispatch_team)} permissions to {DISPATCH_GROUP_NAME}")

            if permissions_for_production_team:
                production_team_group.permissions.add(*permissions_for_production_team)
                print(f"Assigned {len(permissions_for_production_team)} permissions to {PRODUCTION_GROUP_NAME}")
            
            print(f"Custom permissions setup for {self.NAME} completed.")

        except ImportError:
            print(f"Could not import Dispatch models for permission setup in {self.NAME}. Dispatch-related permissions will not be set.")
        except Exception as e_outer:
            # Catch any other unexpected errors during the permission setup process
            print(f"An unexpected error occurred during custom permissions setup for {self.NAME}: {e_outer}")


    def setup_signals(self):
        """
        Connects signal handlers.
        """
        if not stockitem_saved or not StockItemModel:
            print(f"Skipping signal connection for {self.NAME} due to missing imports.")
            return

        print(f"Attempting to connect stockitem_saved signal for {self.NAME}")
        try:
            new_dispatch_uid = f"{self.SLUG}_on_stock_item_saved_handler"
            stockitem_saved.connect(
                self.on_stock_item_saved, 
                sender=StockItemModel,
                dispatch_uid=new_dispatch_uid
            )
            print(f"Successfully connected stockitem_saved for {self.NAME} with UID {new_dispatch_uid}")
        except Exception as e: 
            print(f"An unexpected error occurred during signal connection for {self.NAME}: {e}")

    def on_stock_item_saved(self, sender, instance, created, **kwargs): 
        if not isinstance(instance, StockItemModel):
             print(f"Signal on_stock_item_saved called with non-StockItemModel instance: {type(instance)}. Skipping PN generation.")
             return

        print(f"Signal on_stock_item_saved triggered for instance PK: {instance.pk}, created: {created}")

        should_generate = False
        if created:
            print(f"Instance {instance.pk} is newly created.")
            should_generate = True
        elif not instance.product_number:
            print(f"Instance {instance.pk} has no product number.")
            should_generate = True
        else:
            print(f"Instance {instance.pk} already has a product number: {instance.product_number}. No PN generation needed.")

        if should_generate:
            print(f"Generating PN for instance {instance.pk}...")
            current_dispatch_uid = f"{self.SLUG}_on_stock_item_saved_handler" # Define before try block
            try:
                pn = generate_pn(instance)
                print(f"Generated PN: {pn} for instance {instance.pk}")
                instance.product_number = pn
                
                print(f"Disconnecting signal {current_dispatch_uid} for instance {instance.pk} before save.")
                stockitem_saved.disconnect(self.on_stock_item_saved, sender=StockItemModel, dispatch_uid=current_dispatch_uid)
                
                instance.save(update_fields=['product_number'])
                print(f"Instance {instance.pk} saved with new product_number: {instance.product_number}")
            
            except Exception as e: 
                print(f"Error generating or saving PN for instance {instance.pk}: {e}")
            finally:
                print(f"Reconnecting signal {current_dispatch_uid} for instance {instance.pk} after save attempt.")
                stockitem_saved.connect(self.on_stock_item_saved, sender=StockItemModel, dispatch_uid=current_dispatch_uid)
        else:
            print(f"PN generation skipped for instance {instance.pk}.")

    def get_plugin_urls(self):
        return [
            path('dispatch/', include((dispatch_urls, 'dispatch'), namespace='dispatch')),
        ]

try:
    registry.register(InvenTreeCustomPlugin)
    print(f"Plugin {InvenTreeCustomPlugin.NAME} registered successfully.")
except Exception as e:
    print(f"Error registering plugin {InvenTreeCustomPlugin.NAME if 'InvenTreeCustomPlugin' in globals() else 'Unnamed Plugin'}: {e}")
