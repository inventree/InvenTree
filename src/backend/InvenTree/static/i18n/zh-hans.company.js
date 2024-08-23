

/* globals
    clearFormErrors,
    constructLabel,
    constructForm,
    enableSubmitButton,
    formatCurrency,
    formatDecimal,
    formatDate,
    handleFormErrors,
    handleFormSuccess,
    imageHoverIcon,
    inventreeGet,
    inventreePut,
    hideFormInput,
    loadTableFilters,
    makeDeleteButton,
    makeEditButton,
    makeIconBadge,
    orderParts,
    renderClipboard,
    renderDate,
    renderLink,
    renderPart,
    setupFilterList,
    showFormInput,
    thumbnailImage,
    wrapButtons,
    yesNoLabel,
*/

/* exported
    createAddress,
    createCompany,
    createContact,
    createManufacturerPart,
    createSupplierPart,
    createSupplierPartPriceBreak,
    deleteAddress,
    deleteContacts,
    deleteManufacturerParts,
    deleteManufacturerPartParameters,
    deleteSupplierParts,
    duplicateSupplierPart,
    editAddress,
    editCompany,
    editContact,
    editSupplierPartPriceBreak,
    loadAddressTable,
    loadCompanyTable,
    loadContactTable,
    loadManufacturerPartTable,
    loadManufacturerPartParameterTable,
    loadSupplierPartTable,
    loadSupplierPriceBreakTable,
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
        title: '添加制造商',
        fields: function() {
            var company_fields = companyFormFields();

            company_fields.is_manufacturer.value = true;

            return company_fields;
        }
    };

    constructForm('/api/company/part/manufacturer/', {
        fields: fields,
        method: 'POST',
        title: '添加制造商零件',
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
        title: '编辑制造商零件',
        onSuccess: options.onSuccess
    });
}


function supplierPartFields(options={}) {

    var fields = {
        part: {
            filters: {
                purchaseable: true,
            }
        },
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
            icon: 'fa-sticky-note',
        },
        packaging: {
            icon: 'fa-box',
        },
        pack_quantity: {},
    };

    if (options.part) {
        fields.manufacturer_part.filters.part = options.part;
    }

    return fields;
}

/*
 * Launch a form to create a new SupplierPart
 */
function createSupplierPart(options={}) {

    var fields = supplierPartFields({
        part: options.part,
    });

    if (options.part) {
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
        title: '添加供应商',
        fields: function() {
            var company_fields = companyFormFields();

            company_fields.is_supplier.value = true;

            return company_fields;
        }
    };

    // Add a secondary modal for the manufacturer part
    fields.manufacturer_part.secondary = {
        title: '添加制造商零件',
        fields: function(data) {
            var mp_fields = manufacturerPartFields();

            if (data.part) {
                mp_fields.part.value = data.part;
                mp_fields.part.hidden = true;
            }

            return mp_fields;
        }
    };

    var header = '';
    if (options.part) {
        var part_model = {};
        inventreeGet(`/api/part/${options.part}/`, {}, {
            async: false,
            success: function(response) {
                part_model = response;
            }
        });
        header = constructLabel('Base Part', {});
        header += renderPart(part_model);
        header += `<div>&nbsp;</div>`;
    }

    constructForm('/api/company/part/', {
        fields: fields,
        method: 'POST',
        title: '添加供应商零件',
        onSuccess: options.onSuccess,
        header_html: header,
    });
}


/*
 * Launch a modal form to duplicate an existing SupplierPart instance
 */
function duplicateSupplierPart(part, options={}) {

    var fields = options.fields || supplierPartFields();

    // Retrieve information for the supplied part
    inventreeGet(`/api/company/part/${part}/`, {}, {
        success: function(data) {

            // Remove fields which we do not want to duplicate
            delete data['pk'];
            delete data['available'];
            delete data['availability_updated'];

            constructForm('/api/company/part/', {
                method: 'POST',
                fields: fields,
                title: '重复供应商零件',
                data: data,
                onSuccess: function(response) {
                    handleFormSuccess(response, options);
                }
            });
        }
    });
}


/*
 * Launch a modal form to edit an existing SupplierPart instance
 */
function editSupplierPart(part, options={}) {

    var fields = options.fields || supplierPartFields();

    // Hide the "part" field
    if (fields.part) {
        fields.part.hidden = true;
    }

    constructForm(`/api/company/part/${part}/`, {
        fields: fields,
        title: options.title || '编辑供应商零件',
        onSuccess: options.onSuccess
    });
}


/*
 * Delete one or more SupplierPart objects from the database.
 * - User will be provided with a modal form, showing all the parts to be deleted.
 * - Delete operations are performed sequentially, not simultaneously
 */
function deleteSupplierParts(parts, options={}) {

    if (parts.length == 0) {
        return;
    }

    function renderPartRow(sup_part) {
        var part = sup_part.part_detail;
        var thumb = thumbnailImage(part.thumbnail || part.image);
        var supplier = '-';
        var MPN = '-';

        if (sup_part.supplier_detail) {
            supplier = sup_part.supplier_detail.name;
        }

        if (sup_part.manufacturer_part_detail) {
            MPN = sup_part.manufacturer_part_detail.MPN;
        }

        return `
        <tr>
            <td>${thumb} ${part.full_name}</td>
            <td>${sup_part.SKU}</td>
            <td>${supplier}</td>
            <td>${MPN}</td>
        </tr>`;
    }

    var rows = '';
    var ids = [];

    parts.forEach(function(sup_part) {
        rows += renderPartRow(sup_part);
        ids.push(sup_part.pk);
    });

    var html = `
    <div class='alert alert-block alert-danger'>
    所有选中的供应商零件将被删除
    </div>
    <table class='table table-striped table-condensed'>
    <tr>
        <th>零件</th>
        <th>库存量单位</th>
        <th>供应商</th>
        <th>制造商零件编号</th>
    </tr>
    ${rows}
    </table>
    `;

    constructForm('/api/company/part/', {
        method: 'DELETE',
        multi_delete: true,
        title: '删除供应商零件',
        preFormContent: html,
        form_data: {
            items: ids,
        },
        onSuccess: options.success,
    });
}


/* Construct set of fields for SupplierPartPriceBreak form */
function supplierPartPriceBreakFields(options={}) {
    let fields = {
        part: {
            hidden: true,
        },
        quantity: {},
        price: {
            icon: 'fa-dollar-sign',
        },
        price_currency: {
            icon: 'fa-coins',
        },
    };

    return fields;
}

/* Create a new SupplierPartPriceBreak instance */
function createSupplierPartPriceBreak(part_id, options={}) {

    let fields = supplierPartPriceBreakFields(options);

    fields.part.value = part_id;

    constructForm('/api/company/price-break/', {
        fields: fields,
        method: 'POST',
        title: '添加批发价折扣',
        onSuccess: function(response) {
            handleFormSuccess(response, options);
        }
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
        is_customer: {},
        active: {},
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
            title: '编辑公司',
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
        '/api/company/',
        {
            method: 'POST',
            fields: fields,
            follow: true,
            title: '添加新公司',
        }
    );
}


/*
 * Load company listing data into specified table.
 *
 * Args:
 * - table: Table element on the page
 * - url: Base URL for the API query
 * - options: table options.
 */
function loadCompanyTable(table, url, options={}) {

    let params = options.params || {};
    let filters = loadTableFilters('company', params);

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
            title: '公司',
            sortable: true,
            switchable: false,
            formatter: function(value, row) {
                var html = imageHoverIcon(row.image) + renderLink(value, row.url);

                if (row.is_customer) {
                    html += `<span title='客户' class='fas fa-user-tie float-right'></span>`;
                }

                if (row.is_manufacturer) {
                    html += `<span title='制造商' class='fas fa-industry float-right'></span>`;
                }

                if (row.is_supplier) {
                    html += `<span title='供应商' class='fas fa-building float-right'></span>`;
                }

                return html;
            }
        },
        {
            field: 'description',
            title: '描述',
        },
        {
            field: 'active',
            title: '激活',
            sortable: true,
            switchable: true,
            formatter: function(value) {
                return yesNoLabel(value);
            }
        },
        {
            field: 'website',
            title: '网站',
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
            title: '零件已提供',
            formatter: function(value, row) {
                return renderLink(value, `/company/${row.pk}/?display=supplier-parts`);
            }
        });
    } else if (options.pagetype == 'manufacturers') {
        columns.push({
            sortable: true,
            field: 'parts_manufactured',
            title: '零件已制造',
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
            return '未找到该公司信息';
        },
        showColumns: true,
        name: options.pagetype || 'company',
        columns: columns,
    });
}


/*
 * Construct a set of form fields for the Contact model
 */
function contactFields(options={}) {

    let fields = {
        company: {
            icon: 'fa-building',
        },
        name: {
            icon: 'fa-user',
        },
        phone: {
            icon: 'fa-phone'
        },
        email: {
            icon: 'fa-at',
        },
        role: {
            icon: 'fa-user-tag',
        },
    };

    if (options.company) {
        fields.company.value = options.company;
    }

    return fields;
}


/*
 * Launches a form to create a new Contact
 */
function createContact(options={}) {
    let fields = options.fields || contactFields(options);

    constructForm('/api/company/contact/', {
        method: 'POST',
        fields: fields,
        title: '创建新的联系人',
        onSuccess: function(response) {
            handleFormSuccess(response, options);
        }
    });
}


/*
 * Launches a form to edit an existing Contact
 */
function editContact(pk, options={}) {
    let fields = options.fields || contactFields(options);

    constructForm(`/api/company/contact/${pk}/`, {
        fields: fields,
        title: '编辑联系人',
        onSuccess: function(response) {
            handleFormSuccess(response, options);
        }
    });
}


/*
 * Launches a form to delete one (or more) contacts
 */
function deleteContacts(contacts, options={}) {

    if (contacts.length == 0) {
        return;
    }

    function renderContact(contact) {
        return `
        <tr>
            <td>${contact.name}</td>
            <td>${contact.email}</td>
            <td>${contact.role}</td>
        </tr>`;
    }

    let rows = '';
    let ids = [];

    contacts.forEach(function(contact) {
        rows += renderContact(contact);
        ids.push(contact.pk);
    });

    // eslint-disable-next-line no-useless-escape
    let html = `
    <div class='alert alert-block alert-danger'>
    所有选定的联系人都将被删除
    </div>
    <table class='table table-striped table-condensed'>
    <tr>
        <th>名稱</th>
        <th>电子邮件</th>
        <th>职位</th>
    </tr>
    ${rows}
    </table>`;

    constructForm('/api/company/contact/', {
        method: 'DELETE',
        multi_delete: true,
        title: '删除联系人',
        preFormContent: html,
        form_data: {
            items: ids,
        },
        onSuccess: function(response) {
            handleFormSuccess(response, options);
        }
    });
}


/*
 * Load table listing company contacts
 */
function loadContactTable(table, options={}) {

    var params = options.params || {};

    var filters = loadTableFilters('contact', params);

    setupFilterList('contact', $(table), '#filter-list-contacts');

    $(table).inventreeTable({
        url: '/api/company/contact/',
        queryParams: filters,
        original: params,
        idField: 'pk',
        uniqueId: 'pk',
        sidePagination: 'server',
        formatNoMatches: function() {
            return '未找到联系人';
        },
        showColumns: true,
        name: 'contacts',
        columns: [
            {
                field: 'name',
                title: '名稱',
                sortable: true,
                switchable: false,
            },
            {
                field: 'phone',
                title: '电话号码',
                sortable: false,
                switchable: true,
            },
            {
                field: 'email',
                title: '电子邮件地址',
                sortable: false,
                switchable: true,
            },
            {
                field: 'role',
                title: '职位',
                sortable: false,
                switchable: false,
            },
            {
                field: 'actions',
                title: '',
                sortable: false,
                switchable: false,
                visible: options.allow_edit || options.allow_delete,
                formatter: function(value, row) {
                    var pk = row.pk;

                    let html = '';

                    if (options.allow_edit) {
                        html += makeEditButton('btn-contact-edit', pk, '编辑联系人');
                    }

                    if (options.allow_delete) {
                        html += makeDeleteButton('btn-contact-delete', pk, '删除联系人');
                    }

                    return wrapButtons(html);
                }
            }
        ],
        onPostBody: function() {
            // Edit button callback
            if (options.allow_edit) {
                $(table).find('.btn-contact-edit').click(function() {
                    var pk = $(this).attr('pk');
                    editContact(pk, {
                        onSuccess: function() {
                            $(table).bootstrapTable('refresh');
                        }
                    });
                });
            }

            // Delete button callback
            if (options.allow_delete) {
                $(table).find('.btn-contact-delete').click(function() {
                    var pk = $(this).attr('pk');

                    var row = $(table).bootstrapTable('getRowByUniqueId', pk);

                    if (row && row.pk) {

                        deleteContacts([row], {
                            onSuccess: function() {
                                $(table).bootstrapTable('refresh');
                            }
                        });
                    }
                });
            }
        }
    });
}

/*
 * Construct a set of form fields for the Address model
 */
function addressFields(options={}) {

    let fields = {
        company: {
            icon: 'fa-building',
        },
        primary: {},
        title: {},
        line1: {
            icon: 'fa-map'
        },
        line2: {
            icon: 'fa-map',
        },
        postal_code: {
            icon: 'fa-map-pin',
        },
        postal_city: {
            icon: 'fa-city'
        },
        province: {
            icon: 'fa-map'
        },
        country: {
            icon: 'fa-map'
        },
        shipping_notes: {
            icon: 'fa-shuttle-van'
        },
        internal_shipping_notes: {
            icon: 'fa-clipboard'
        },
        link: {
            icon: 'fa-link'
        }
    };

    if (options.company) {
        fields.company.value = options.company;
    }

    return fields;
}

/*
 * Launches a form to create a new Address
 */
function createAddress(options={}) {
    let fields = options.fields || addressFields(options);

    constructForm('/api/company/address/', {
        method: 'POST',
        fields: fields,
        title: '创建新地址',
        onSuccess: function(response) {
            handleFormSuccess(response, options);
        }
    });
}

/*
 * Launches a form to edit an existing Address
 */
function editAddress(pk, options={}) {
    let fields = options.fields || addressFields(options);

    constructForm(`/api/company/address/${pk}/`, {
        fields: fields,
        title: '编辑地址',
        onSuccess: function(response) {
            handleFormSuccess(response, options);
        }
    });
}

/*
 * Launches a form to delete one (or more) addresses
 */
function deleteAddress(addresses, options={}) {

    if (addresses.length == 0) {
        return;
    }

    function renderAddress(address) {
        return `
        <tr>
            <td>${address.title}</td>
            <td>${address.line1}</td>
            <td>${address.line2}</td>
        </tr>`;
    }

    let rows = '';
    let ids = [];

    addresses.forEach(function(address) {
        rows += renderAddress(address);
        ids.push(address.pk);
    });

    let html = `
    <div class='alert alert-block alert-danger'>
    所有选中的地址将被删除
    </div>
    <table class='table table-striped table-condensed'>
    <tr>
        <th>名稱</th>
        <th>第1行</th>
        <th>第2行</th>
    </tr>
    ${rows}
    </table>`;

    constructForm('/api/company/address/', {
        method: 'DELETE',
        multi_delete: true,
        title: '删除地址',
        preFormContent: html,
        form_data: {
            items: ids,
        },
        onSuccess: function(response) {
            handleFormSuccess(response, options);
        }
    });
}

function loadAddressTable(table, options={}) {
    var params = options.params || {};

    var filters = loadTableFilters('address', params);

    setupFilterList('address', $(table), '#filter-list-addresses');

    $(table).inventreeTable({
        url: '/api/company/address/',
        queryParams: filters,
        original: params,
        idField: 'pk',
        uniqueId: 'pk',
        sidePagination: 'server',
        sortable: true,
        formatNoMatches: function() {
            return '未找到地址';
        },
        showColumns: true,
        name: 'addresses',
        columns: [
            {
                field: 'primary',
                title: '主要的',
                switchable: false,
                formatter: function(value) {
                    return yesNoLabel(value);
                }
            },
            {
                field: 'title',
                title: '标题',
                sortable: true,
                switchable: false,
            },
            {
                field: 'line1',
                title: '第1行',
                sortable: false,
                switchable: false,
            },
            {
                field: 'line2',
                title: '第2行',
                sortable: false,
                switchable: false,
            },
            {
                field: 'postal_code',
                title: '邮政编码',
                sortable: false,
                switchable: false,
            },
            {
                field: 'postal_city',
                title: '邮政编码',
                sortable: false,
                switchable: false,
            },
            {
                field: 'province',
                title: '省/市/自治区',
                sortable: false,
                switchable: false,
            },
            {
                field: 'country',
                title: '国家/地区',
                sortable: false,
                switchable: false,
            },
            {
                field: 'shipping_notes',
                title: '快递单',
                sortable: false,
                switchable: true,
            },
            {
                field: 'internal_shipping_notes',
                title: '内部备注',
                sortable: false,
                switchable: true,
            },
            {
                field: 'link',
                title: '外部連結',
                sortable: false,
                switchable: true,
            },
            {
                field: 'actions',
                title: '',
                sortable: false,
                switchable: false,
                visible: options.allow_edit || options.allow_delete,
                formatter: function(value, row) {
                    var pk = row.pk;

                    let html = '';

                    if (options.allow_edit) {
                        html += makeEditButton('btn-address-edit', pk, '编辑地址');
                    }

                    if (options.allow_delete) {
                        html += makeDeleteButton('btn-address-delete', pk, '删除地址');
                    }

                    return wrapButtons(html);
                }
            }
        ],
        onPostBody: function() {
            // Edit button callback
            if (options.allow_edit) {
                $(table).find('.btn-address-edit').click(function() {
                    var pk = $(this).attr('pk');
                    editAddress(pk, {
                        onSuccess: function() {
                            $(table).bootstrapTable('refresh');
                        }
                    });
                });
            }

            // Delete button callback
            if (options.allow_delete) {
                $(table).find('.btn-address-delete').click(function() {
                    var pk = $(this).attr('pk');

                    var row = $(table).bootstrapTable('getRowByUniqueId', pk);

                    if (row && row.pk) {

                        deleteAddress([row], {
                            onSuccess: function() {
                                $(table).bootstrapTable('refresh');
                            }
                        });
                    }
                });
            }
        }
    });
}

/* Delete one or more ManufacturerPart objects from the database.
 * - User will be provided with a modal form, showing all the parts to be deleted.
 * - Delete operations are performed sequentially, not simultaneously
 */
function deleteManufacturerParts(selections, options={}) {

    if (selections.length == 0) {
        return;
    }

    function renderPartRow(man_part, opts={}) {
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
    var ids = [];

    selections.forEach(function(man_part) {
        rows += renderPartRow(man_part);
        ids.push(man_part.pk);
    });

    var html = `
    <div class='alert alert-block alert-danger'>
    所有选定的制造商零件都将被删除
    </div>
    <table class='table table-striped table-condensed'>
    <tr>
        <th>零件</th>
        <th>制造商零件编号</th>
        <th>制造商</th>
    </tr>
    ${rows}
    </table>
    `;

    constructForm('/api/company/part/manufacturer/', {
        method: 'DELETE',
        multi_delete: true,
        title: '删除制造商零件',
        preFormContent: html,
        form_data: {
            items: ids,
        },
        onSuccess: options.success,
    });
}


function deleteManufacturerPartParameters(selections, options={}) {

    if (selections.length == 0) {
        return;
    }

    function renderParam(param) {
        return `
        <tr>
            <td>${param.name}</td>
            <td>${param.units}</td>
        </tr>`;
    }

    var rows = '';
    var ids = [];

    selections.forEach(function(param) {
        rows += renderParam(param);
        ids.push(param.pk);
    });

    var html = `
    <div class='alert alert-block alert-danger'>
    所有选定的参数都将被删除
    </div>
    <table class='table table-striped table-condensed'>
    <tr>
        <th>名稱</th>
        <th>值</th>
    </tr>
    ${rows}
    </table>
    `;

    constructForm('/api/company/part/manufacturer/parameter/', {
        method: 'DELETE',
        multi_delete: true,
        title: '删除参数',
        preFormContent: html,
        form_data: {
            items: ids,
        },
        onSuccess: options.success,
    });

}


// Construct a set of actions for the manufacturer part table
function makeManufacturerPartActions(options={}) {
    return [
        {
            label: 'order',
            title: '订购零件',
            icon: 'fa-shopping-cart',
            permission: 'purchase_order.add',
            callback: function(data) {
                let parts = [];

                data.forEach(function(item) {
                    let part = item.part_detail;
                    part.manufacturer_part = item.pk;
                    parts.push(part);
                });

                orderParts(parts);
            },
        },
        {
            label: 'delete',
            title: '删除制造商零件',
            icon: 'fa-trash-alt icon-red',
            permission: 'purchase_order.delete',
            callback: function(data) {
                deleteManufacturerParts(data, {
                    success: function() {
                        $('#manufacturer-part-table').bootstrapTable('refresh');
                    }
                });
            },
        }
    ];
}


/*
 * Load manufacturer part table
 */
function loadManufacturerPartTable(table, url, options) {

    // Query parameters
    var params = options.params || {};

    // Load filters
    var filters = loadTableFilters('manufacturer-part', params);

    var filterTarget = options.filterTarget || '#filter-list-manufacturer-part';

    setupFilterList('manufacturer-part', $(table), filterTarget, {
        custom_actions: [
            {
                label: 'manufacturer-part',
                title: '制造商零件操作',
                icon: 'fa-tools',
                actions: makeManufacturerPartActions({
                    manufacturer_id: options.params.manufacturer,
                })
            }
        ]
    });

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
            return '未找到制造商零件';
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
                title: '零件',
                formatter: function(value, row) {

                    var url = `/part/${row.part}/`;

                    var html = imageHoverIcon(row.part_detail.thumbnail) + renderLink(value, url);

                    if (row.part_detail.is_template) {
                        html += makeIconBadge('fa-clone', '模板零件');
                    }

                    if (row.part_detail.assembly) {
                        html += makeIconBadge('fa-tools', '装配零件');
                    }

                    if (!row.part_detail.active) {
                        html += `<span class='badge badge-right rounded-pill bg-warning'>未激活</span>`;
                    }

                    return html;
                }
            },
            {
                sortable: true,
                field: 'manufacturer',
                title: '制造商',
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
                title: '制造商零件编号',
                formatter: function(value, row) {
                    return renderClipboard(renderLink(value, `/manufacturer-part/${row.pk}/`));
                }
            },
            {
                field: 'link',
                title: '連結',
                formatter: function(value) {
                    if (value) {
                        return renderLink(value, value, {external: true});
                    } else {
                        return '';
                    }
                }
            },
            {
                field: 'description',
                title: '描述',
                sortable: false,
                switchable: true,
            },
            {
                field: 'actions',
                title: '',
                sortable: false,
                switchable: false,
                formatter: function(value, row) {
                    let pk = row.pk;
                    let html = '';

                    html += makeEditButton('button-manufacturer-part-edit', pk, '编辑制造商零件');
                    html += makeDeleteButton('button-manufacturer-part-delete', pk, '删除制造商零件');

                    return wrapButtons(html);
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


/*
 * Load table of ManufacturerPartParameter objects
 */
function loadManufacturerPartParameterTable(table, url, options) {

    var params = options.params || {};

    // Load filters
    var filters = loadTableFilters('manufacturer-part-parameters', params);

    setupFilterList('manufacturer-part-parameters', $(table));

    $(table).inventreeTable({
        url: url,
        method: 'get',
        original: params,
        queryParams: filters,
        name: 'manufacturerpartparameters',
        groupBy: false,
        formatNoMatches: function() {
            return '未找到参数';
        },
        columns: [
            {
                checkbox: true,
                switchable: false,
                visible: true,
            },
            {
                field: 'name',
                title: '名稱',
                switchable: false,
                sortable: true,
            },
            {
                field: 'value',
                title: '值',
                switchable: false,
                sortable: true,
            },
            {
                field: 'units',
                title: '单位',
                switchable: true,
                sortable: true,
            },
            {
                field: 'actions',
                title: '',
                switchable: false,
                sortable: false,
                formatter: function(value, row) {
                    let pk = row.pk;
                    let html = '';

                    html += makeEditButton('button-parameter-edit', pk, '编辑参数');
                    html += makeDeleteButton('button-parameter-delete', pk, '删除参数');

                    return wrapButtons(html);
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
                    title: '编辑参数',
                    refreshTable: table,
                });
            });
            $(table).find('.button-parameter-delete').click(function() {
                var pk = $(this).attr('pk');

                constructForm(`/api/company/part/manufacturer/parameter/${pk}/`, {
                    method: 'DELETE',
                    title: '删除参数',
                    refreshTable: table,
                });
            });
        }
    });
}


// Construct a set of actions for the supplier part table
function makeSupplierPartActions(options={}) {
    return [
        {
            label: 'order',
            title: '订购零件',
            icon: 'fa-shopping-cart',
            permission: 'purchase_order.add',
            callback: function(data) {
                let parts = []

                data.forEach(function(entry) {
                    parts.push(entry.part_detail);
                });

                orderParts(parts, {
                    supplier: options.supplier_id,
                });
            },
        },
        {
            label: 'delete',
            title: '删除供应商零件',
            icon: 'fa-trash-alt icon-red',
            permission: 'purchase_order.delete',
            callback: function(data) {
                deleteSupplierParts(data, {
                    success: function() {
                        $('#supplier-part-table').bootstrapTable('refresh');
                    }
                });
            },
        }
    ];
}


/*
 * Load supplier part table
 */
function loadSupplierPartTable(table, url, options) {

    // Query parameters
    var params = options.params || {};

    // Load filters
    var filters = loadTableFilters('supplierpart', params);

    setupFilterList('supplierpart', $(table), '#filter-list-supplier-part', {
        custom_actions: [
            {
                label: 'supplier-part',
                title: '供应商零件操作',
                icon: 'fa-tools',
                actions: makeSupplierPartActions({
                    supplier_id: options.params.supplier,
                }),
            }
        ]
    });

    $(table).inventreeTable({
        url: url,
        method: 'get',
        original: params,
        sidePagination: 'server',
        uniqueId: 'pk',
        queryParams: filters,
        name: 'supplierparts',
        groupBy: false,
        sortable: true,
        formatNoMatches: function() {
            return '未找到供应商零件';
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
                sortName: 'part',
                title: '零件',
                formatter: function(value, row) {

                    var url = `/part/${row.part}/`;

                    var html = imageHoverIcon(row.part_detail.thumbnail) + renderLink(value, url);

                    if (row.part_detail.is_template) {
                        html += makeIconBadge('fa-clone', '模板零件');
                    }

                    if (row.part_detail.assembly) {
                        html += makeIconBadge('fa-tools', '装配零件');
                    }

                    if (!row.part_detail.active) {
                        html += `<span class='badge badge-right rounded-pill bg-warning'>未激活</span>`;
                    }

                    return html;
                }
            },
            {
                sortable: true,
                field: 'supplier',
                title: '供应商',
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
                title: '供应商零件',
                formatter: function(value, row) {
                    return renderClipboard(renderLink(value, `/supplier-part/${row.pk}/`));
                }
            },
            {
                visible: params['manufacturer_detail'],
                switchable: params['manufacturer_detail'],
                sortable: true,
                sortName: 'manufacturer',
                field: 'manufacturer_detail.name',
                title: '制造商',
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
                sortName: 'MPN',
                field: 'manufacturer_part_detail.MPN',
                title: '制造商零件编号',
                formatter: function(value, row) {
                    if (value && row.manufacturer_part) {
                        return renderClipboard(renderLink(value, `/manufacturer-part/${row.manufacturer_part}/`));
                    } else {
                        return '-';
                    }
                }
            },
            {
                field: 'description',
                title: '描述',
                sortable: false,
            },
            {
                field: 'packaging',
                title: '打包',
                sortable: true,
            },
            {
                field: 'pack_quantity',
                title: '包装数量',
                sortable: true,
                formatter: function(value, row) {

                    let html = '';

                    if (value) {
                        html = value;
                    } else {
                        html = '-';
                    }

                    if (row.part_detail && row.part_detail.units) {
                        html += `<span class='fas fa-info-circle float-right' title='基础单位: ${row.part_detail.units}'></span>`;
                    }

                    return html;
                }
            },
            {
                field: 'link',
                sortable: false,
                title: '連結',
                formatter: function(value) {
                    if (value) {
                        return renderLink(value, value, {external: true});
                    } else {
                        return '';
                    }
                }
            },
            {
                field: 'note',
                title: '备注',
                sortable: false,
            },
            {
                field: 'in_stock',
                title: '有库存',
                sortable: true,
            },
            {
                field: 'available',
                title: '可用性',
                sortable: true,
                formatter: function(value, row) {
                    if (row.availability_updated) {
                        let html = formatDecimal(value);
                        let date = renderDate(row.availability_updated, {showTime: true});

                        html += makeIconBadge(
                            'fa-info-circle',
                            `最近更新: ${date}`
                        );
                        return html;
                    } else {
                        return '-';
                    }
                }
            },
            {
                field: 'updated',
                title: '最近更新',
                sortable: true,
            },
            {
                field: 'actions',
                title: '',
                sortable: false,
                switchable: false,
                formatter: function(value, row) {
                    let pk = row.pk;
                    let html = '';

                    html += makeEditButton('button-supplier-part-edit', pk, '编辑供应商零件');
                    html += makeDeleteButton('button-supplier-part-delete', pk, '删除供应商零件');

                    return wrapButtons(html);
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
                var row = $(table).bootstrapTable('getRowByUniqueId', pk);

                deleteSupplierParts(
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


/*
 * Load a table of supplier price break data
 */
function loadSupplierPriceBreakTable(options={}) {

    var table = options.table || $('#price-break-table');

    // Setup button callbacks once table is loaded
    function setupCallbacks() {
        table.find('.button-price-break-delete').click(function() {
            var pk = $(this).attr('pk');

            constructForm(`/api/company/price-break/${pk}/`, {
                method: 'DELETE',
                title: '删除批发价',
                refreshTable: table,
            });
        });

        table.find('.button-price-break-edit').click(function() {
            var pk = $(this).attr('pk');

            constructForm(`/api/company/price-break/${pk}/`, {
                fields: supplierPartPriceBreakFields(),
                title: '编辑批发价',
                refreshTable: table,
            });
        });
    }

    setupFilterList('supplierpricebreak', table, '#filter-list-supplierpricebreak');

    table.inventreeTable({
        name: 'buypricebreaks',
        url: '/api/company/price-break/',
        queryParams: {
            part: options.part,
        },
        formatNoMatches: function() {
            return '找不到批发价信息';
        },
        onPostBody: function() {
            setupCallbacks();
        },
        columns: [
            {
                field: 'pk',
                title: 'ID',
                visible: false,
                switchable: false,
            },
            {
                field: 'quantity',
                title: '數量',
                sortable: true,
            },
            {
                field: 'price',
                title: '价格',
                sortable: true,
                formatter: function(value, row, index) {
                    return formatCurrency(value, {
                        currency: row.price_currency
                    });
                }
            },
            {
                field: 'updated',
                title: '最近更新',
                sortable: true,
                formatter: function(value, row) {
                    var html = renderDate(value);

                    let buttons = '';

                    buttons += makeEditButton('button-price-break-edit', row.pk, '编辑批发价');
                    buttons += makeDeleteButton('button-price-break-delete', row.pk, '删除批发价');

                    html += wrapButtons(buttons);

                    return html;
                }
            },
        ]
    });
}
