"""Django views for interacting with common models."""

from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.utils.translation import gettext_lazy as _

from crispy_forms.helper import FormHelper
from formtools.wizard.views import NamedUrlSessionWizardView, SessionWizardView

from InvenTree.views import AjaxView

from . import forms
from .files import FileManager


class InvenTreeMultiStepMixin():
    """Mixin to setup basic methods of multi-step forms."""

    form_steps_template = []
    form_steps_description = []
    file_manager = None
    media_folder = ''
    file_storage = FileSystemStorage(settings.MEDIA_ROOT)

    def __init__(self, *args, **kwargs):
        """Override init method to set media folder."""
        super().__init__(**kwargs)

        self.process_media_folder()

    def process_media_folder(self):
        """Process media folder."""
        if self.media_folder:
            media_folder_abs = settings.MEDIA_ROOT.joinpath(self.media_folder)
            if not media_folder_abs.exists():
                media_folder_abs.mkdir(parents=True, exist_ok=True)
            self.file_storage = FileSystemStorage(location=media_folder_abs)

    def get_template_names(self):
        """Select template."""
        try:
            # Get template
            template = self.form_steps_template[self.steps.index]
        except IndexError:
            return self.template_name

        return template

    def get_context_data(self, **kwargs):
        """Update context data."""
        # Retrieve current context
        context = super().get_context_data(**kwargs)

        # Get form description
        try:
            description = self.form_steps_description[self.steps.index]
        except IndexError:
            description = ''
        # Add description to form steps
        context.update({'description': description})

        return context


class MultiStepFormView(InvenTreeMultiStepMixin, SessionWizardView):
    """Setup basic methods of multi-step form.

    Needs:
    - form_list: list of forms
    - form_steps_description: description for each form
    """
    pass


class NamedMultiStepFormView(InvenTreeMultiStepMixin, NamedUrlSessionWizardView):
    """Setup basic methods of multi-step form.

    Needs:
    - form_list: list of forms
    - form_steps_description: description for each form
    """
    pass


class FileManagementFormView(MultiStepFormView):
    """File management form wizard.

    Perform the following steps:
        1. Upload tabular data file
        2. Match headers to InvenTree fields
        3. Edit row data and match InvenTree items
    """

    name = None
    form_list = [
        ('upload', forms.UploadFileForm),
        ('fields', forms.MatchFieldForm),
        ('items', forms.MatchItemForm),
    ]
    form_steps_description = [
        _("Upload File"),
        _("Match Fields"),
        _("Match Items"),
    ]
    media_folder = 'file_upload/'
    extra_context_data = {}

    def __init__(self, *args, **kwargs):
        """Initialize the FormView."""
        # Perform all checks and inits for MultiStepFormView
        super().__init__(self, *args, **kwargs)

        # Check for file manager class
        if not hasattr(self, 'file_manager_class') and not issubclass(self.file_manager_class, FileManager):
            raise NotImplementedError('A subclass of a file manager class needs to be set!')

    def get_context_data(self, form=None, **kwargs):
        """Handle context data."""
        if form is None:
            form = self.get_form()

        context = super().get_context_data(form=form, **kwargs)

        if self.steps.current in ('fields', 'items'):

            # Get columns and row data
            self.columns = self.file_manager.columns()
            self.rows = self.file_manager.rows()
            # Check for stored data
            stored_data = self.storage.get_step_data(self.steps.current)
            if stored_data:
                self.get_form_table_data(stored_data)
            elif self.steps.current == 'items':
                # Set form table data
                self.set_form_table_data(form=form)

            # Update context
            context.update({'rows': self.rows})
            context.update({'columns': self.columns})

        # Load extra context data
        for key, items in self.extra_context_data.items():
            context.update({key: items})

        return context

    def get_file_manager(self, step=None, form=None):
        """Get FileManager instance from uploaded file."""
        if self.file_manager:
            return

        if step is not None:
            # Retrieve stored files from upload step
            upload_files = self.storage.get_step_files('upload')
            if upload_files:
                # Get file
                file = upload_files.get('upload-file', None)
                if file:
                    self.file_manager = self.file_manager_class(file=file, name=self.name)

    def get_form_kwargs(self, step=None):
        """Update kwargs to dynamically build forms."""
        # Always retrieve FileManager instance from uploaded file
        self.get_file_manager(step)

        if step == 'upload':
            # Dynamically build upload form
            if self.name:
                kwargs = {
                    'name': self.name
                }
                return kwargs
        elif step == 'fields':
            # Dynamically build match field form
            kwargs = {
                'file_manager': self.file_manager
            }
            return kwargs
        elif step == 'items':
            # Dynamically build match item form
            kwargs = {}
            kwargs['file_manager'] = self.file_manager

            # Get data from fields step
            data = self.storage.get_step_data('fields')

            # Process to update columns and rows
            self.rows = self.file_manager.rows()
            self.columns = self.file_manager.columns()
            self.get_form_table_data(data)
            self.set_form_table_data()
            self.get_field_selection()

            kwargs['row_data'] = self.rows

            return kwargs

        return super().get_form_kwargs()

    def get_form(self, step=None, data=None, files=None):
        """Add crispy-form helper to form."""
        form = super().get_form(step=step, data=data, files=files)

        form.helper = FormHelper()
        form.helper.form_show_labels = False

        return form

    def get_form_table_data(self, form_data):
        """Extract table cell data from form data and fields. These data are used to maintain state between sessions.

        Table data keys are as follows:

            col_name_<idx> - Column name at idx as provided in the uploaded file
            col_guess_<idx> - Column guess at idx as selected
            row_<x>_col<y> - Cell data as provided in the uploaded file
        """
        # Map the columns
        self.column_names = {}
        self.column_selections = {}

        self.row_data = {}

        for item, value in form_data.items():

            # Column names as passed as col_name_<idx> where idx is an integer

            # Extract the column names
            if item.startswith('col_name_'):
                try:
                    col_id = int(item.replace('col_name_', ''))
                except ValueError:
                    continue

                self.column_names[col_id] = value

            # Extract the column selections (in the 'select fields' view)
            if item.startswith('fields-'):

                try:
                    col_name = item.replace('fields-', '')
                except ValueError:
                    continue

                for idx, name in self.column_names.items():
                    if name == col_name:
                        self.column_selections[idx] = value
                        break

            # Extract the row data
            if item.startswith('row_'):
                # Item should be of the format row_<r>_col_<c>
                s = item.split('_')

                if len(s) < 4:
                    continue

                # Ignore row/col IDs which are not correct numeric values
                try:
                    row_id = int(s[1])
                    col_id = int(s[3])
                except ValueError:
                    continue

                if row_id not in self.row_data:
                    self.row_data[row_id] = {}

                self.row_data[row_id][col_id] = value

    def set_form_table_data(self, form=None):
        """Set the form table data."""
        if self.column_names:
            # Re-construct the column data
            self.columns = []

            for idx, value in self.column_names.items():
                header = ({
                    'name': value,
                    'guess': self.column_selections.get(idx, ''),
                })
                self.columns.append(header)

        if self.row_data:
            # Re-construct the row data
            self.rows = []

            # Update the row data
            for row_idx, row_key in enumerate(sorted(self.row_data.keys())):
                row_data = self.row_data[row_key]

                data = []

                for idx, item in row_data.items():
                    column_data = {
                        'name': self.column_names[idx],
                        'guess': self.column_selections[idx],
                    }

                    cell_data = {
                        'cell': item,
                        'idx': idx,
                        'column': column_data,
                    }
                    data.append(cell_data)

                row = {
                    'index': row_idx,
                    'data': data,
                    'errors': {},
                }

                self.rows.append(row)

        # In the item selection step: update row data with mapping to form fields
        if form and self.steps.current == 'items':
            # Find field keys
            field_keys = []
            for field in form.fields:
                field_key = field.split('-')[0]
                if field_key not in field_keys:
                    field_keys.append(field_key)

            # Populate rows
            for row in self.rows:
                for field_key in field_keys:
                    # Map row data to field
                    row[field_key] = field_key + '-' + str(row['index'])

    def get_column_index(self, name):
        """Return the index of the column with the given name.

        It named column is not found, return -1
        """
        try:
            idx = list(self.column_selections.values()).index(name)
        except ValueError:
            idx = -1

        return idx

    def get_field_selection(self):
        """Once data columns have been selected, attempt to pre-select the proper data from the database. This function is called once the field selection has been validated. The pre-fill data are then passed through to the part selection form.

        This method is very specific to the type of data found in the file,
        therefore overwrite it in the subclass.
        """
        pass

    def get_clean_items(self):
        """Returns dict with all cleaned values."""
        items = {}

        for form_key, form_value in self.get_all_cleaned_data().items():
            # Split key from row value
            try:
                (field, idx) = form_key.split('-')
            except ValueError:
                continue

            try:
                if idx not in items:
                    # Insert into items
                    items.update({
                        idx: {
                            self.form_field_map[field]: form_value,
                        }
                    })
                else:
                    # Update items
                    items[idx][self.form_field_map[field]] = form_value
            except KeyError:
                pass

        return items

    def check_field_selection(self, form):
        """Check field matching."""
        # Are there any missing columns?
        missing_columns = []

        # Check that all required fields are present
        for col in self.file_manager.REQUIRED_HEADERS:
            if col not in self.column_selections.values():
                missing_columns.append(col)

        # Check that at least one of the part match field is present
        part_match_found = False
        for col in self.file_manager.ITEM_MATCH_HEADERS:
            if col in self.column_selections.values():
                part_match_found = True
                break

        # If not, notify user
        if not part_match_found:
            for col in self.file_manager.ITEM_MATCH_HEADERS:
                missing_columns.append(col)

        # Track any duplicate column selections
        duplicates = []

        for col in self.column_names:

            if col in self.column_selections:
                guess = self.column_selections[col]
            else:
                guess = None

            if guess:
                n = list(self.column_selections.values()).count(self.column_selections[col])
                if n > 1 and self.column_selections[col] not in duplicates:
                    duplicates.append(self.column_selections[col])

        # Store extra context data
        self.extra_context_data = {
            'missing_columns': missing_columns,
            'duplicates': duplicates,
        }

        # Data validation
        valid = not missing_columns and not duplicates

        return valid

    def validate(self, step, form):
        """Validate forms."""
        valid = True

        # Get form table data
        self.get_form_table_data(form.data)

        if step == 'fields':
            # Validate user form data
            valid = self.check_field_selection(form)

            if not valid:
                form.add_error(None, _('Fields matching failed'))

        elif step == 'items':
            pass

        return valid

    def post(self, request, *args, **kwargs):
        """Perform validations before posting data."""
        wizard_goto_step = self.request.POST.get('wizard_goto_step', None)

        form = self.get_form(data=self.request.POST, files=self.request.FILES)

        form_valid = self.validate(self.steps.current, form)

        if not form_valid and not wizard_goto_step:
            # Re-render same step
            return self.render(form)

        return super().post(*args, **kwargs)


class FileManagementAjaxView(AjaxView):
    """Use a FileManagementFormView as base for a AjaxView Inherit this class before inheriting the base FileManagementFormView.

    ajax_form_steps_template: templates for rendering ajax
    validate: function to validate the current form -> normally point to the same function in the base FileManagementFormView
    """

    def post(self, request):
        """Handle wizard step call.

        Possible actions:
        - Step back -> render previous step
        - Invalid  form -> render error
        - Valid form and not done -> render next step
        - Valid form and done -> render final step
        """
        # check if back-step button was selected
        wizard_back = self.request.POST.get('act-btn_back', None)
        if wizard_back:
            back_step_index = self.get_step_index() - 1
            self.storage.current_step = list(self.get_form_list().keys())[back_step_index]
            return self.renderJsonResponse(request, data={'form_valid': None})

        # validate form
        form = self.get_form(data=self.request.POST, files=self.request.FILES)
        form_valid = self.validate(self.steps.current, form)

        # check if valid
        if not form_valid:
            return self.renderJsonResponse(request, data={'form_valid': None})

        # store the cleaned data and files.
        self.storage.set_step_data(self.steps.current, self.process_step(form))
        self.storage.set_step_files(self.steps.current, self.process_step_files(form))

        # check if the current step is the last step
        if self.steps.current == self.steps.last:
            # call done - to process data, returned response is not used
            self.render_done(form)
            data = {'form_valid': True, 'success': _('Parts imported')}
            return self.renderJsonResponse(request, data=data)
        else:
            self.storage.current_step = self.steps.next

        return self.renderJsonResponse(request, data={'form_valid': None})

    def get(self, request):
        """Reset storage if flag is set, proceed to render JsonResponse."""
        if 'reset' in request.GET:
            # reset form
            self.storage.reset()
            self.storage.current_step = self.steps.first
        return self.renderJsonResponse(request)

    def renderJsonResponse(self, request, form=None, data=None, context=None):
        """Always set the right templates before rendering."""
        # Set default - see B006
        if data is None:
            data = {}

        self.setTemplate()
        return super().renderJsonResponse(request, form=form, data=data, context=context)

    def get_data(self) -> dict:
        """Get extra context data."""
        data = super().get_data()
        data['hideErrorMessage'] = '1'  # hide the error
        buttons = [{'name': 'back', 'title': _('Previous Step')}] if self.get_step_index() > 0 else []
        data['buttons'] = buttons  # set buttons
        return data

    def setTemplate(self):
        """Set template name and title."""
        self.ajax_template_name = self.ajax_form_steps_template[self.get_step_index()]
        self.ajax_form_title = self.form_steps_description[self.get_step_index()]

    def validate(self, obj, form, **kwargs):
        """Generic validate action.

        This is the point to process provided userinput.
        """
        raise NotImplementedError('This function needs to be overridden!')
