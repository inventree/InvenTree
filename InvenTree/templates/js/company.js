{% load i18n %}


// Returns a default form-set for creating / editing a Company object
function companyFormFields(options={}) {

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
};

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

    var filters = loadTableFilters("company");

    for (var key in params) {
        filters[key] = params[key];
    }

    setupFilterList("company", $(table));

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
            formatter: function(value, row, index, field) {
                var html = imageHoverIcon(row.image) + renderLink(value, row.url);

                if (row.is_customer) {
                    html += `<span title='{% trans "Customer" %}' class='fas fa-user-tie label-right'></span>`;
                }

                if (row.is_manufacturer) {
                    html += `<span title='{% trans "Manufacturer" %}' class='fas fa-industry label-right'></span>`;
                }

                if (row.is_supplier) {
                    html += `<span title='{% trans "Supplier" %}' class='fas fa-building label-right'></span>`;
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
            formatter: function(value, row, index, field) {
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
                return renderLink(value, `/company/${row.pk}/parts/`);
            }
        });
    } else if (options.pagetype == 'manufacturers') {
        columns.push({
            sortable: true,
            field: 'parts_manufactured',
            title: '{% trans "Parts Manufactured" %}',
            formatter: function(value, row) {
                return renderLink(value, `/company/${row.pk}/parts/`);
            }
        });
    }

    $(table).inventreeTable({
        url: url,
        method: 'get',
        queryParams: filters,
        groupBy: false,
        sidePagination: 'server',
        formatNoMatches: function() { return "{% trans "No company information found" %}"; },
        showColumns: true,
        name: options.pagetype || 'company',
        columns: columns,
    });
}


function deleteManufacturerParts(selections, options={}) {

    if (selections.length == 0) {
        return;
    }

    var parts = [];

    var text = `
        <div class='alert alert-block alert-danger'>
            <p>{% trans "The following manufacturer parts will be deleted" %}:</p>
            <ul>`;

        selections.forEach(function(item) {
            parts.push(item.pk);

            text += `
            <li>
                <p>${item.MPN} - ${item.part_detail.full_name}</p>
            </li>`;
        });
                
        text += `
            </ul>
        </div>`;

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
                $.when.apply($, requests).then(function() {

                    if (options.onSuccess) {
                        options.onSuccess();
                    }
                })
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
    var filters = loadTableFilters("manufacturer-part");

    for (var key in params) {
        filters[key] = params[key];
    }

    setupFilterList("manufacturer-part", $(table));

    $(table).inventreeTable({
        url: url,
        method: 'get',
        original: params,
        queryParams: filters,
        name: 'manufacturerparts',
        groupBy: false,
        formatNoMatches: function() { return '{% trans "No manufacturer parts found" %}'; },
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
                formatter: function(value, row, index, field) {

                    var url = `/part/${row.part}/`;

                    var html = imageHoverIcon(row.part_detail.thumbnail) + renderLink(value, url);

                    if (row.part_detail.is_template) {
                        html += `<span class='fas fa-clone label-right' title='{% trans "Template part" %}'></span>`;
                    }

                    if (row.part_detail.assembly) {
                        html += `<span class='fas fa-tools label-right' title='{% trans "Assembled part" %}'></span>`;
                    }

                    if (!row.part_detail.active) {
                        html += `<span class='label label-warning label-right'>{% trans "Inactive" %}</span>`;
                    }

                    return html;
                }
            },
            {
                sortable: true,
                field: 'manufacturer',
                title: '{% trans "Manufacturer" %}',
                formatter: function(value, row, index, field) {
                    if (value && row.manufacturer_detail) {
                        var name = row.manufacturer_detail.name;
                        var url = `/company/${value}/`;
                        var html = imageHoverIcon(row.manufacturer_detail.image) + renderLink(name, url);

                        return html;
                    } else {
                        return "-";
                    }
                }
            },
            {
                sortable: true,
                field: 'MPN',
                title: '{% trans "MPN" %}',
                formatter: function(value, row, index, field) {
                    return renderLink(value, `/manufacturer-part/${row.pk}/`);
                }
            },
            {
                field: 'link',
                title: '{% trans "Link" %}',
                formatter: function(value, row, index, field) {
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
            }
        ],
    });
}


function loadManufacturerPartParameterTable(table, url, options) {
    /*
     * Load table of ManufacturerPartParameter objects
     */

    var params = options.params || {};

    // Load filters
    var filters = loadTableFilters("manufacturer-part-parameters");

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
        formatNoMatches: function() { return '{% trans "No parameters found" %}'; },
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
    var filters = loadTableFilters("supplier-part");

    for (var key in params) {
        filters[key] = params[key];
    }

    setupFilterList("supplier-part", $(table));

    $(table).inventreeTable({
        url: url,
        method: 'get',
        original: params,
        queryParams: filters,
        name: 'supplierparts',
        groupBy: false,
        formatNoMatches: function() { return '{% trans "No supplier parts found" %}'; },
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
                formatter: function(value, row, index, field) {

                    var url = `/part/${row.part}/`;

                    var html = imageHoverIcon(row.part_detail.thumbnail) + renderLink(value, url);

                    if (row.part_detail.is_template) {
                        html += `<span class='fas fa-clone label-right' title='{% trans "Template part" %}'></span>`;
                    }

                    if (row.part_detail.assembly) {
                        html += `<span class='fas fa-tools label-right' title='{% trans "Assembled part" %}'></span>`;
                    }

                    if (!row.part_detail.active) {
                        html += `<span class='label label-warning label-right'>{% trans "Inactive" %}</span>`;
                    }

                    return html;
                }
            },
            {
                sortable: true,
                field: 'supplier',
                title: '{% trans "Supplier" %}',
                formatter: function(value, row, index, field) {
                    if (value) {
                        var name = row.supplier_detail.name;
                        var url = `/company/${value}/`; 
                        var html = imageHoverIcon(row.supplier_detail.image) + renderLink(name, url);

                        return html;
                    } else {
                        return "-";
                    }
                },
            },
            {
                sortable: true,
                field: 'SKU',
                title: '{% trans "Supplier Part" %}',
                formatter: function(value, row, index, field) {
                    return renderLink(value, `/supplier-part/${row.pk}/`);
                }
            },
            {
                visible: params['manufacturer_detail'],
                switchable: params['manufacturer_detail'],
                sortable: true,
                field: 'manufacturer',
                title: '{% trans "Manufacturer" %}',
                formatter: function(value, row, index, field) {
                    if (value && row.manufacturer_detail) {
                        var name = row.manufacturer_detail.name;
                        var url = `/company/${value}/`;
                        var html = imageHoverIcon(row.manufacturer_detail.image) + renderLink(name, url);

                        return html;
                    } else {
                        return "-";
                    }
                }
            },
            {
                visible: params['manufacturer_detail'],
                switchable: params['manufacturer_detail'],
                sortable: true,
                field: 'MPN',
                title: '{% trans "MPN" %}',
                formatter: function(value, row, index, field) {
                    if (value && row.manufacturer_part) {
                        return renderLink(value, `/manufacturer-part/${row.manufacturer_part.pk}/`);
                    } else {
                        return "-";
                    }
                }
            },
            {
                field: 'link',
                title: '{% trans "Link" %}',
                formatter: function(value, row, index, field) {
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
            }
        ],
    });
}