{% load i18n %}

/* globals
    constructForm,
    imageHoverIcon,
    inventreeDelete,
    loadTableFilters,
    makeIconButton,
    renderLink,
    setupFilterList,
    showQuestionDialog,
*/

/* exported
    createCompany,
    createManufacturerPart,
    createSupplierPart,
    deleteManufacturerParts,
    editCompany,
    loadCompanyTable,
    loadManufacturerPartTable,
    loadManufacturerPartParameterTable,
    loadSupplierPartTable,
*/


/**
 * Construct a set of form fields for creating / editing a ManufacturerPart
 * @returns
 */
function manufacturerPartFields() {

    return {
        part: {},
        manufacturer: {},
        MPN: {
            icon: 'fa-hashtag',
        },
        description: {},
        link: {
            icon: 'fa-link',
        }
    };
}


/**
 * Launches a form to create a new ManufacturerPart
 * @param {object} options
 */
function createManufacturerPart(options={}) {

    var fields = manufacturerPartFields();

    if (options.part) {
        fields.part.value = options.part;
        fields.part.hidden = true;
    }

    if (options.manufacturer) {
        fields.manufacturer.value = options.manufacturer;
    }

    fields.manufacturer.secondary = {
        title: '{% trans "Add Manufacturer" %}',
        fields: function() {
            var company_fields = companyFormFields();

            company_fields.is_manufacturer.value = true;

            return company_fields;
        }
    };

    constructForm('{% url "api-manufacturer-part-list" %}', {
        fields: fields,
        method: 'POST',
        title: '{% trans "Add Manufacturer Part" %}',
        onSuccess: options.onSuccess
    });
}


/**
 * Launches a form to edit a ManufacturerPart
 * @param {integer} part - ID of a ManufacturerPart
 * @param {object} options
 */
function editManufacturerPart(part, options={}) {

    var url = `/api/company/part/manufacturer/${part}/`;

    var fields = manufacturerPartFields();

    fields.part.hidden = true;

    constructForm(url, {
        fields: fields,
        title: '{% trans "Edit Manufacturer Part" %}',
        onSuccess: options.onSuccess
    });
}


function supplierPartFields() {

    return {
        part: {},
        manufacturer_part: {
            filters: {
                part_detail: true,
                manufacturer_detail: true,
            },
            auto_fill: true,
        },
        supplier: {},
        SKU: {
            icon: 'fa-hashtag',
        },
        description: {},
        link: {
            icon: 'fa-link',
        },
        note: {
            icon: 'fa-pencil-alt',
        },
        packaging: {
            icon: 'fa-box',
        }
    };
}

/*
 * Launch a form to create a new ManufacturerPart
 */
function createSupplierPart(options={}) {

    var fields = supplierPartFields();

    if (options.part) {
        fields.manufacturer_part.filters.part = options.part;
        fields.part.hidden = true;
        fields.part.value = options.part;
    }

    if (options.supplier) {
        fields.supplier.value = options.supplier;
    }

    if (options.manufacturer_part) {
        fields.manufacturer_part.value = options.manufacturer_part;
    }

    // Add a secondary modal for the supplier
    fields.supplier.secondary = {
        title: '{% trans "Add Supplier" %}',
        fields: function() {
            var company_fields = companyFormFields();

            company_fields.is_supplier.value = true;

            return company_fields;
        }
    };

    // Add a secondary modal for the manufacturer part
    fields.manufacturer_part.secondary = {
        title: '{% trans "Add Manufacturer Part" %}',
        fields: function(data) {
            var mp_fields = manufacturerPartFields();

            if (data.part) {
                mp_fields.part.value = data.part;
                mp_fields.part.hidden = true;
            }

            return mp_fields;
        }
    };

    constructForm('{% url "api-supplier-part-list" %}', {
        fields: fields,
        method: 'POST',
        title: '{% trans "Add Supplier Part" %}',
        onSuccess: options.onSuccess,
    });
}


function editSupplierPart(part, options={}) {

    var fields = supplierPartFields();

    // Hide the "part" field
    fields.part.hidden = true;

    constructForm(`/api/company/part/${part}/`, {
        fields: fields,
        title: '{% trans "Edit Supplier Part" %}',
        onSuccess: options.onSuccess
    });
}


function deleteSupplierPart(part, options={}) {

    constructForm(`/api/company/part/${part}/`, {
        method: 'DELETE',
        title: '{% trans "Delete Supplier Part" %}',
        onSuccess: options.onSuccess,
    });
}


// Returns a default form-set for creating / editing a Company object
function companyFormFields() {

    return {
        name: {},
        description: {},
        website: {
            icon: 'fa-globe',
        },
        address: {
            icon: 'fa-envelope',
        },
        currency: {
            icon: 'fa-dollar-sign',
        },
        phone: {
            icon: 'fa-phone',
        },
        email: {
            icon: 'fa-at',
        },
        contact: {
            icon: 'fa-address-card',
        },
        is_supplier: {},
        is_manufacturer: {},
        is_customer: {}
    };
}


function editCompany(pk, options={}) {

    var fields = options.fields || companyFormFields();

    constructForm(
        `/api/company/${pk}/`,
        {
            method: 'PATCH',
            fields: fields,
            reload: true,
            title: '{% trans "Edit Company" %}',
        }
    );
}

/*
 * Launches a form to create a new company.
 * As this can be called from many different contexts,
 * we abstract it here!
 */
function createCompany(options={}) {

    // Default field set
    var fields = options.fields || companyFormFields();

    constructForm(
        '{% url "api-company-list" %}',
        {
            method: 'POST',
            fields: fields,
            follow: true,
            title: '{% trans "Add new Company" %}',
        }
    );
}


function loadCompanyTable(table, url, options={}) {
    /*
     * Load company listing data into specified table.
     *
     * Args:
     * - table: Table element on the page
     * - url: Base URL for the API query
     * - options: table options.
     */

    // Query parameters
    var params = options.params || {};

    var filters = loadTableFilters('company');

    for (var key in params) {
        filters[key] = params[key];
    }

    setupFilterList('company', $(table));

    var columns = [
        {
            field: 'pk',
            title: 'ID',
            visible: false,
            switchable: false,
        },
        {
            field: 'name',
            title: '{% trans "Company" %}',
            sortable: true,
            switchable: false,
            formatter: function(value, row) {
                var html = imageHoverIcon(row.image) + renderLink(value, row.url);

                if (row.is_customer) {
                    html += `<span title='{% trans "Customer" %}' class='fas fa-user-tie float-right'></span>`;
                }

                if (row.is_manufacturer) {
                    html += `<span title='{% trans "Manufacturer" %}' class='fas fa-industry float-right'></span>`;
                }

                if (row.is_supplier) {
                    html += `<span title='{% trans "Supplier" %}' class='fas fa-building float-right'></span>`;
                }

                return html;
            }
        },
        {
            field: 'description',
            title: '{% trans "Description" %}',
        },
        {
            field: 'website',
            title: '{% trans "Website" %}',
            formatter: function(value) {
                if (value) {
                    return renderLink(value, value);
                }
                return '';
            }
        },
    ];

    if (options.pagetype == 'suppliers') {
        columns.push({
            sortable: true,
            field: 'parts_supplied',
            title: '{% trans "Parts Supplied" %}',
            formatter: function(value, row) {
                return renderLink(value, `/company/${row.pk}/?display=supplier-parts`);
            }
        });
    } else if (options.pagetype == 'manufacturers') {
        columns.push({
            sortable: true,
            field: 'parts_manufactured',
            title: '{% trans "Parts Manufactured" %}',
            formatter: function(value, row) {
                return renderLink(value, `/company/${row.pk}/?display=manufacturer-parts`);
            }
        });
    }

    $(table).inventreeTable({
        url: url,
        method: 'get',
        queryParams: filters,
        original: params,
        groupBy: false,
        sidePagination: 'server',
        formatNoMatches: function() {
            return '{% trans "No company information found" %}';
        },
        showColumns: true,
        name: options.pagetype || 'company',
        columns: columns,
    });
}


/* Delete one or more ManufacturerPart objects from the database.
 */
function deleteManufacturerParts(selections, options={}) {

    if (selections.length == 0) {
        return;
    }

    function renderPart(man_part, opts={}) {
        var part = man_part.part_detail;
        var thumb = thumbnailImage(part.thumbnail || part.image);

        return `
        <tr>
            <td>${thumb} ${part.full_name}</td>
            <td>${man_part.MPN}</td>
            <td>${man_part.manufacturer_detail.name}</td>
        </tr>`;
    }

    var rows = '';

    selections.forEach(function(man_part) {
        rows += renderPart(man_part);
    });

    var html = `
    <div class='alert alert-block alert-danger'>
    {% trans "All selected manufacturer parts will be deleted" %}
    </div>
    <table class='table table-striped table-condensed'>
    <tr>
        <th>{% trans "Part" %}</th>
        <th>{% trans "MPN" %}</th>
        <th>{% trans "Manufacturer" %}</th>
    </tr>
    ${rows}
    </table>
    `;

    constructFormBody({}, {
        title: '{% trans "Delete Manufacturer Parts" %}',
        preFormContent: html,
        submitText: '{% trans "Delete" %}',
        submitClass: 'danger',
        confirm: true,
        onSubmit: function(fields, opts) {
            // Delete each item one at a time, so we don't overload the database
            showModalSpinner(opts.modal);

            function deleteNextPart() {
                if (selections.length > 0) {
                    var part = selections.shift();

                    inventreeDelete(`/api/company/part/manufacturer/${part.pk}/`, {
                        complete: deleteNextPart,
                    });
                } else {
                    $(opts.modal).modal('hide');

                    if (options.success) {
                        options.success();
                    }
                }
            }

            deleteNextPart();
        }
    });

    return;

    showQuestionDialog(
        '{% trans "Delete Manufacturer Parts" %}',
        text,
        {
            accept_text: '{% trans "Delete" %}',
            accept: function() {

                // Delete each manufacturer part
                var requests = [];

                parts.forEach(function(pk) {
                    var url = `/api/company/part/manufacturer/${pk}`;

                    requests.push(inventreeDelete(url));
                });

                // Wait for all the requests to complete
                $.when.apply($, requests).done(function() {

                    if (options.onSuccess) {
                        options.onSuccess();
                    }
                });
            }
        }
    );
}


function loadManufacturerPartTable(table, url, options) {
    /*
     * Load manufacturer part table
     *
     */

    // Query parameters
    var params = options.params || {};

    // Load filters
    var filters = loadTableFilters('manufacturer-part');

    for (var key in params) {
        filters[key] = params[key];
    }

    var filterTarget = options.filterTarget || '#filter-list-manufacturer-part';

    setupFilterList('manufacturer-part', $(table), filterTarget);

    $(table).inventreeTable({
        url: url,
        method: 'get',
        original: params,
        queryParams: filters,
        uniqueId: 'pk',
        sidePagination: 'server',
        name: 'manufacturerparts',
        groupBy: false,
        formatNoMatches: function() {
            return '{% trans "No manufacturer parts found" %}';
        },
        columns: [
            {
                checkbox: true,
                switchable: false,
            },
            {
                visible: params['part_detail'],
                switchable: params['part_detail'],
                sortable: true,
                field: 'part_detail.full_name',
                title: '{% trans "Part" %}',
                formatter: function(value, row) {

                    var url = `/part/${row.part}/`;

                    var html = imageHoverIcon(row.part_detail.thumbnail) + renderLink(value, url);

                    if (row.part_detail.is_template) {
                        html += `<span class='fas fa-clone float-right' title='{% trans "Template part" %}'></span>`;
                    }

                    if (row.part_detail.assembly) {
                        html += `<span class='fas fa-tools float-right' title='{% trans "Assembled part" %}'></span>`;
                    }

                    if (!row.part_detail.active) {
                        html += `<span class='badge badge-right rounded-pill bg-warning'>{% trans "Inactive" %}</span>`;
                    }

                    return html;
                }
            },
            {
                sortable: true,
                field: 'manufacturer',
                title: '{% trans "Manufacturer" %}',
                formatter: function(value, row) {
                    if (value && row.manufacturer_detail) {
                        var name = row.manufacturer_detail.name;
                        var url = `/company/${value}/`;
                        var html = imageHoverIcon(row.manufacturer_detail.image) + renderLink(name, url);

                        return html;
                    } else {
                        return '-';
                    }
                }
            },
            {
                sortable: true,
                field: 'MPN',
                title: '{% trans "MPN" %}',
                formatter: function(value, row) {
                    return renderLink(value, `/manufacturer-part/${row.pk}/`);
                }
            },
            {
                field: 'link',
                title: '{% trans "Link" %}',
                formatter: function(value) {
                    if (value) {
                        return renderLink(value, value);
                    } else {
                        return '';
                    }
                }
            },
            {
                field: 'description',
                title: '{% trans "Description" %}',
                sortable: false,
                switchable: true,
            },
            {
                field: 'actions',
                title: '',
                sortable: false,
                switchable: false,
                formatter: function(value, row) {
                    var pk = row.pk;

                    var html = `<div class='btn-group float-right' role='group'>`;

                    html += makeIconButton('fa-edit icon-blue', 'button-manufacturer-part-edit', pk, '{% trans "Edit manufacturer part" %}');
                    html += makeIconButton('fa-trash-alt icon-red', 'button-manufacturer-part-delete', pk, '{% trans "Delete manufacturer part" %}');

                    html += '</div>';

                    return html;
                }
            }
        ],
        onPostBody: function() {
            // Callbacks
            $(table).find('.button-manufacturer-part-edit').click(function() {
                var pk = $(this).attr('pk');

                editManufacturerPart(
                    pk,
                    {
                        onSuccess: function() {
                            $(table).bootstrapTable('refresh');
                        }
                    }
                );
            });

            $(table).find('.button-manufacturer-part-delete').click(function() {
                var pk = $(this).attr('pk');
                var row = $(table).bootstrapTable('getRowByUniqueId', pk);

                deleteManufacturerParts(
                    [row],
                    {
                        success: function() {
                            $(table).bootstrapTable('refresh');
                        }
                    }
                );
            });
        }
    });
}


function loadManufacturerPartParameterTable(table, url, options) {
    /*
     * Load table of ManufacturerPartParameter objects
     */

    var params = options.params || {};

    // Load filters
    var filters = loadTableFilters('manufacturer-part-parameters');

    // Overwrite explicit parameters
    for (var key in params) {
        filters[key] = params[key];
    }

    // setupFilterList("manufacturer-part-parameters", $(table));

    $(table).inventreeTable({
        url: url,
        method: 'get',
        original: params,
        queryParams: filters,
        name: 'manufacturerpartparameters',
        groupBy: false,
        formatNoMatches: function() {
            return '{% trans "No parameters found" %}';
        },
        columns: [
            {
                checkbox: true,
                switchable: false,
                visible: true,
            },
            {
                field: 'name',
                title: '{% trans "Name" %}',
                switchable: false,
                sortable: true,
            },
            {
                field: 'value',
                title: '{% trans "Value" %}',
                switchable: false,
                sortable: true,
            },
            {
                field: 'units',
                title: '{% trans "Units" %}',
                switchable: true,
                sortable: true,
            },
            {
                field: 'actions',
                title: '',
                switchable: false,
                sortable: false,
                formatter: function(value, row) {

                    var pk = row.pk;

                    var html = `<div class='btn-group float-right' role='group'>`;

                    html += makeIconButton('fa-edit icon-blue', 'button-parameter-edit', pk, '{% trans "Edit parameter" %}');
                    html += makeIconButton('fa-trash-alt icon-red', 'button-parameter-delete', pk, '{% trans "Delete parameter" %}');

                    html += `</div>`;

                    return html;
                }
            }
        ],
        onPostBody: function() {
            // Setup callback functions
            $(table).find('.button-parameter-edit').click(function() {
                var pk = $(this).attr('pk');

                constructForm(`/api/company/part/manufacturer/parameter/${pk}/`, {
                    fields: {
                        name: {},
                        value: {},
                        units: {},
                    },
                    title: '{% trans "Edit Parameter" %}',
                    onSuccess: function() {
                        $(table).bootstrapTable('refresh');
                    }
                });
            });
            $(table).find('.button-parameter-delete').click(function() {
                var pk = $(this).attr('pk');

                constructForm(`/api/company/part/manufacturer/parameter/${pk}/`, {
                    method: 'DELETE',
                    title: '{% trans "Delete Parameter" %}',
                    onSuccess: function() {
                        $(table).bootstrapTable('refresh');
                    }
                });
            });
        }
    });
}


function loadSupplierPartTable(table, url, options) {
    /*
     * Load supplier part table
     *
     */

    // Query parameters
    var params = options.params || {};

    // Load filters
    var filters = loadTableFilters('supplier-part');

    for (var key in params) {
        filters[key] = params[key];
    }

    setupFilterList('supplier-part', $(table));

    $(table).inventreeTable({
        url: url,
        method: 'get',
        original: params,
        sidePagination: 'server',
        queryParams: filters,
        name: 'supplierparts',
        groupBy: false,
        formatNoMatches: function() {
            return '{% trans "No supplier parts found" %}';
        },
        columns: [
            {
                checkbox: true,
                switchable: false,
            },
            {
                visible: params['part_detail'],
                switchable: params['part_detail'],
                sortable: true,
                field: 'part_detail.full_name',
                title: '{% trans "Part" %}',
                formatter: function(value, row) {

                    var url = `/part/${row.part}/`;

                    var html = imageHoverIcon(row.part_detail.thumbnail) + renderLink(value, url);

                    if (row.part_detail.is_template) {
                        html += `<span class='fas fa-clone float-right' title='{% trans "Template part" %}'></span>`;
                    }

                    if (row.part_detail.assembly) {
                        html += `<span class='fas fa-tools float-right' title='{% trans "Assembled part" %}'></span>`;
                    }

                    if (!row.part_detail.active) {
                        html += `<span class='badge badge-right rounded-pill bg-warning'>{% trans "Inactive" %}</span>`;
                    }

                    return html;
                }
            },
            {
                sortable: true,
                field: 'supplier',
                title: '{% trans "Supplier" %}',
                formatter: function(value, row) {
                    if (value) {
                        var name = row.supplier_detail.name;
                        var url = `/company/${value}/`;
                        var html = imageHoverIcon(row.supplier_detail.image) + renderLink(name, url);

                        return html;
                    } else {
                        return '-';
                    }
                },
            },
            {
                sortable: true,
                field: 'SKU',
                title: '{% trans "Supplier Part" %}',
                formatter: function(value, row) {
                    return renderLink(value, `/supplier-part/${row.pk}/`);
                }
            },
            {
                visible: params['manufacturer_detail'],
                switchable: params['manufacturer_detail'],
                sortable: true,
                field: 'manufacturer_detail.name',
                title: '{% trans "Manufacturer" %}',
                formatter: function(value, row) {
                    if (value && row.manufacturer_detail) {
                        var name = value;
                        var url = `/company/${row.manufacturer_detail.pk}/`;
                        var html = imageHoverIcon(row.manufacturer_detail.image) + renderLink(name, url);

                        return html;
                    } else {
                        return '-';
                    }
                }
            },
            {
                visible: params['manufacturer_detail'],
                switchable: params['manufacturer_detail'],
                sortable: true,
                field: 'manufacturer_part_detail.MPN',
                title: '{% trans "MPN" %}',
                formatter: function(value, row) {
                    if (value && row.manufacturer_part) {
                        return renderLink(value, `/manufacturer-part/${row.manufacturer_part}/`);
                    } else {
                        return '-';
                    }
                }
            },
            {
                field: 'link',
                title: '{% trans "Link" %}',
                formatter: function(value) {
                    if (value) {
                        return renderLink(value, value);
                    } else {
                        return '';
                    }
                }
            },
            {
                field: 'description',
                title: '{% trans "Description" %}',
                sortable: false,
            },
            {
                field: 'note',
                title: '{% trans "Notes" %}',
                sortable: false,
            },
            {
                field: 'packaging',
                title: '{% trans "Packaging" %}',
                sortable: false,
            },
            {
                field: 'actions',
                title: '',
                sortable: false,
                switchable: false,
                formatter: function(value, row) {
                    var pk = row.pk;

                    var html = `<div class='btn-group float-right' role='group'>`;

                    html += makeIconButton('fa-edit icon-blue', 'button-supplier-part-edit', pk, '{% trans "Edit supplier part" %}');
                    html += makeIconButton('fa-trash-alt icon-red', 'button-supplier-part-delete', pk, '{% trans "Delete supplier part" %}');

                    html += '</div>';

                    return html;
                }
            }
        ],
        onPostBody: function() {
            // Callbacks
            $(table).find('.button-supplier-part-edit').click(function() {
                var pk = $(this).attr('pk');

                editSupplierPart(
                    pk,
                    {
                        onSuccess: function() {
                            $(table).bootstrapTable('refresh');
                        }
                    }
                );
            });

            $(table).find('.button-supplier-part-delete').click(function() {
                var pk = $(this).attr('pk');

                deleteSupplierPart(
                    pk,
                    {
                        onSuccess: function() {
                            $(table).bootstrapTable('refresh');
                        }
                    }
                );
            });
        }
    });
}
