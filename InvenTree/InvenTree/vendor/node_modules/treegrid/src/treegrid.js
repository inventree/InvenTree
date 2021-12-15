//main options
//target: div element, where create grid
//id: report id (info for backend)
//url: backend handler for grid
function TreeGrid(opt) {
    //addition options
    var def = {
        sort: true, //Allow sort
        sort_num_desc: true, //Numeric columns sort desc first
        dad_col: true, //Drag and drop columns
        resize_col: true, //Resize columns
        resize_tab: true, //Resize table
        titlebar: true, //Display titlebar
        hide_btn: true, //Show/hide columns
        min_btn: true, //Minimize
        max_btn: true //Maximize
    };

    this.opt = $.extend({}, def, opt);

    //all texts in grid
    this.opt.text_max = "Maximize";
    this.opt.text_min = "Minimize";
    this.opt.text_res = "Restore";
    this.opt.text_hide = "Show/hide columns";
    this.opt.text_app = "Apply";
    this.opt.text_close = "Close";
    this.opt.text_def = "Default";
    this.opt.text_sel_f = "Select columns";

    this.$mainDiv = $(opt.target);
    if (this.$mainDiv.length == 0)
        throw new Error('Target not specified');
    if (this.$mainDiv.length > 1)
        throw new Error('Multiple target specified');
    this.$mainDiv.addClass('grid-main');

    this.$mainDiv.off().html('');

    //if parent size not specified, switch to autosize mode
    var $e = this.$mainDiv.clone().appendTo('body').wrap('<div style="display: none"></div>');
    var cs = window.getComputedStyle
        ? getComputedStyle($e[0], null)
        : $e[0].currentStyle;
    this.autoSize = cs.width == 'auto' && cs.height == 'auto';
    if (this.autoSize) {
        this.opt.resize_tab = false;
        this.opt.max_btn = false;
    }
    $e.parent().remove();
}

TreeGrid.prototype = {
    //starting method
    init: function (orderBy) {
        var obj = this;
        this.params = { id: this.opt.id };
        if (orderBy)
            this.params.orderBy = orderBy;
        this.$mainDiv.append('<div class="grid-loader"></div>');
        this.saveSetting();
        this.columnPosition = null;
        $.ajax({ type: this.opt.method || 'POST', cache: false, url: this.opt.url, data: this.params})
        .done(function (data) {
            if (obj.dataColumns)
                data.Columns = obj.dataColumns;
            obj.fillData(data);
            $('.grid-loader', obj.$mainDiv).remove();
            obj.restoreSettings();
        })
        .fail(function () {
            obj.ajax_error(arguments);
        });
    },
    saveSetting: function () {
        var $cols = $('.grid-header-colgroup col', this.$mainDiv);
        this.colWidth = [];
        for (var i = 0; i < $cols.length; i++) {
            var w = $cols.eq(i).width();
            this.colWidth.push(w);
        }

        this.scrollLeft = 0;
        if (this.$dataDiv != null)
            this.scrollLeft = this.$dataDiv.scrollLeft();
    },
    restoreSettings: function () {
        var sizeChanged = false;
        if (this.colWidth) {
            var totalWidth = 0;
            var $cols = $('.grid-header-colgroup col', this.$mainDiv);
            var $cols2 = $('.grid-data-colgroup col', this.$mainDiv);
            for (var i = 0; i < this.colWidth.length; i++) {
                var w = this.colWidth[i];
                $cols.eq(i).attr('width', w).css('width', w + 'px');
                $cols2.eq(i).attr('width', w).css('width', w + 'px');
                totalWidth += w;
            }
            $('.grid-header-table', this.$mainDiv).width(totalWidth);
            sizeChanged = true;
        }

        if (this.scrollLeft)
            this.$dataDiv.scrollLeft(this.scrollLeft);

        //restore active row
        if (this.activeRowId) {
            var trActive = this.$dataDiv.find('tr[rowid="' + this.activeRowId + '"]').first();
            if (trActive.length > 0) {
                this.rowClick(trActive);
            }
        }

        if (sizeChanged)
            this._resize();
    },
    ajax_error: function (xhr, status, err) {
        var msg = 'error';
        if (xhr.length > 0) {
            if (xhr[0].responseText)
                msg = xhr[0].responseText;
            else if (xhr[0].status)
                msg = this.opt.url + ': ' + xhr[0].status + ' - ' + xhr[0].statusText;;
        }
        this.opt.target.html(msg);
    },
    fillData: function (data) {
        this.$mainDiv.off().html('');

        var obj = this;
        this.changeColumns(data);

        this.columns = [];
        this.header = this.headerTable(data.Columns, this.columns);
        this.dataColumns = data.Columns;

        if (this.opt.titlebar)
            this.createTitlebar(data);

        this.createTable(data);
        this.bindEvents(data);

        if (data.OrderByColumn != null) {
            var colNum = 0;
            var asc = true;
            var found = false;
            var orderByColumn = data.OrderByColumn.toLowerCase();
            if (orderByColumn.substr(orderByColumn.length - 5) == " desc") {
                asc = false;
                orderByColumn = orderByColumn.substr(0, orderByColumn.length - 5);
            }
            for (i = 0; i < this.columns.length; i++) {
                c = this.columns[i];
                if (c.Hidden)
                    continue;
                colNum++;
                if (c.Name.toLowerCase() == orderByColumn) {
                    found = true;
                    break;
                }
            }
            if (found && colNum != 0)
                this.showSort(colNum - 1, asc);
        }

        if (data.ExpandFirstLevel) {
            var $div = this.$dataTable.find('.grid-group.grid-plus');
            for (var i = 0; i < $div.length; i++) {
                var $item = $div.eq(i);
                this.doGroupClick($item, true);
            }
        }
    },
    createTitlebar: function (data) {
        var obj = this;

        var buttons = "<div class='grid-buttons'>";
        if (this.opt.max_btn)
            buttons += "<div title='" + this.opt.text_max + "' class='grid-btn-max'></div>";
        if (this.opt.min_btn)
            buttons += "<div title='" + this.opt.text_min + "' class='grid-btn-min'></div>";
        if (this.opt.hide_btn)
            buttons += "<div title='" + this.opt.text_hide + "' class='grid-btn-hide'></div>";
        buttons += "</div>";
        var tb = "<div class='grid-toolbar'>" + buttons + "<div class='grid-title'>" + (data.Caption || '') + "</div></div>";
        this.$mainDiv.append(tb);
        this.$toolbar = this.$mainDiv.find('.grid-toolbar');

        $('.grid-btn-max, .grid-btn-unmax', this.$mainDiv).click(function () {
            if ($(this).hasClass('grid-btn-max')) {
                $(this).removeClass('grid-btn-max').addClass('grid-btn-unmax').attr('title', obj.opt.text_res);

                if ($('.grid-btn-unmin', obj.$mainDiv).length > 0)
                    unmin();

                obj.normalWidth = obj.normalWidth || obj.$mainDiv.prop('style')['width'];
                obj.normalHeight = obj.normalHeight || obj.$mainDiv.prop('style')['height'];

                var totalHeight = obj.$headerDiv.height() + obj.$dataTable.height() + 25;
                var totalWidth = obj.$dataTable.width() + 20;
                if (this.$toolbar) {
                    totalHeight += obj.$toolbar.height();
                }
                obj.$mainDiv.width(totalWidth)
                    .height(totalHeight)
                    .addClass('grid-max');
                $('.grid-resizer', obj.$mainDiv).hide();
            }
            else if ($(this).hasClass('grid-btn-unmax')) {
                unmax();
            }
            obj._resize();
        });

        function unmax() {
            $('.grid-btn-unmax', obj.$mainDiv).removeClass('grid-btn-unmax').addClass('grid-btn-max').attr('title', obj.opt.text_max);

            obj.$mainDiv.prop('style')['width'] = obj.normalWidth;
            obj.$mainDiv.prop('style')['height'] = obj.normalHeight;
            obj.$mainDiv.removeClass('grid-max');
            obj.normalWidth = obj.normalHeight = obj.dataHeight = null;
            $('.grid-resizer', obj.$mainDiv).show();
        }

        $('.grid-btn-min, .grid-btn-unmin', this.$mainDiv).click(function () {
            if ($(this).hasClass('grid-btn-min')) {
                $(this).removeClass('grid-btn-min').addClass('grid-btn-unmin').attr('title', obj.opt.text_res);

                if ($('.grid-btn-unmax', obj.$mainDiv).length > 0)
                    unmax();

                obj.normalWidth = obj.normalWidth || obj.$mainDiv.prop('style')['width'];
                obj.normalHeight = obj.normalHeight || obj.$mainDiv.prop('style')['height'];
                obj.dataHeight = obj.$dataDiv.height();

                obj.$mainDiv.height(obj.$toolbar.height())
                    .addClass('grid-min');
                $('.grid-resizer', obj.$mainDiv).hide();
            }
            else if ($(this).hasClass('grid-btn-unmin')) {
                unmin();
            }
            obj._resize();
        });

        function unmin() {
            $('.grid-btn-unmin', obj.$mainDiv).removeClass('grid-btn-unmin').addClass('grid-btn-min').attr('title', obj.opt.text_min);

            obj.$mainDiv.prop('style')['width'] = obj.normalWidth;
            obj.$mainDiv.prop('style')['height'] = obj.normalHeight;
            obj.$mainDiv.removeClass('grid-min');
            obj.$dataDiv.height(obj.dataHeight);
            obj.$headerDiv.show()
            obj.normalWidth = obj.normalHeight = obj.dataHeight = null;
            $('.grid-resizer', obj.$mainDiv).show();
        }

        var hideDiv = '<div class="grid-hide">';
        hideDiv += '<table class="grid-hide-table"><tr><th>' + this.opt.text_sel_f + '</th></tr></table>';

        var globalHeaderId = 1;
        var headerDictionary = {};

        hideDiv += '<div class="grid-tree">';
        hideDiv += '<ul class="grid-tree-ul">' + addUlGrid(data.Columns, true) + '</ul>';
        hideDiv += '</div>';

        hideDiv += '<table class="grid-tree-bottom"><tr><td><div class="grid-hide-btn-apply">' + this.opt.text_app +
            '</div></td><td><div class="grid-hide-btn-close">' + this.opt.text_close +
            '</div></td><td><div class="grid-hide-btn-default">' + this.opt.text_def + '</div></td></tr></table></div>';
        $('.grid-toolbar', this.$mainDiv).before(hideDiv);

        //expand/collapse tree in Show/hide columns dialog
        $('.grid-tree', this.$mainDiv).click(function (e) {
            var $node = $(e.target);
            if ($node.is('.grid-tree-expand')) {
                $node = $node.parent();
            }
            else if ($node.is('a') || $node.is('.grid-tree-check')) {
                if ($node.is('.grid-tree-check'))
                    $node = $node.parent();

                var $check = $node.find('.grid-tree-check');
                var $allCheck = $check.parents('li').eq(0).find('.grid-tree-check');
                var $siblingCheck = $check.parents('li').eq(0).parent().find('.grid-tree-check');
                var $parentCheck = $check.parents('li').eq(0).parents('li').eq(0).find('.grid-tree-check').eq(0);
                if ($check.is('.checked')) {
                    $allCheck.removeClass('checked');
                    if (!$siblingCheck.hasClass('checked')) $parentCheck.removeClass('checked');
                }
                else {
                    $allCheck.addClass('checked');
                    $parentCheck.addClass('checked');
                }
                return false;
            }
            else {
                return false;
            }

            if (!$node.hasClass('grid-tree-node'))
                return false;

            if ($node.hasClass('leaf'))
                return false;

            if ($node.find('li').length > 0) {
                if (!$node.hasClass('grid-tree-node'))
                    return;
                if ($node.hasClass('closed'))
                    $node.removeClass('closed').addClass('open');
                else if ($node.hasClass('open'))
                    $node.removeClass('open').addClass('closed');

                return false;
            }

            var id = $node.attr('nodeId');
            this.loadData(id, $node);

            return false;
        });

        this.$mainDiv.on('click', '.grid-btn-hide', function () {
            var $hidden = obj.$mainDiv.find('.grid-hide .grid-tree-check');
            $hidden.each(function () {
                var id = $(this).data('id');
                var h = headerDictionary[id];
                if (h.Hidden == null) return;
                if (!h.Hidden) $(this).addClass('checked');
                else $(this).removeClass('checked');
            });
            $('.grid-hide', obj.$mainDiv).slideDown();

            return false;
        });

        this.$mainDiv.on('click', '.grid-hide-btn-apply', function () {
            var $hidden = obj.$mainDiv.find('.grid-hide .grid-tree-check');
            var anyColumn = false;
            $hidden.each(function () {
                var id = $(this).data('id');
                var hidden = !$(this).hasClass('checked');
                if (!hidden) {
                    anyColumn = true;
                    return;
                }
            });
            if (!anyColumn)
                return false;

            $hidden.each(function () {
                var id = $(this).data('id');
                var hidden = !$(this).hasClass('checked');
                var h = headerDictionary[id];
                h.Hidden = hidden;
            });
            $('.grid-hide', obj.$mainDiv).fadeOut();
            obj.fillData(data);
            return false;
        });

        this.$mainDiv.on('click', '.grid-hide-btn-default', function () {
            var $hidden = obj.$mainDiv.find('.grid-hide .grid-tree-check');
            $hidden.each(function () {
                var id = $(this).data('id');
                var h = headerDictionary[id];
                var hidden = h.HiddenDefault;
                if (!hidden)
                    $(this).addClass('checked');
                else
                    $(this).removeClass('checked');
            });
            return false;
        });

        $('.grid-hide-btn-close', this.$mainDiv).on('click', function () {
            $('.grid-hide', obj.$mainDiv).slideUp();
            return false;
        });

        function addUlGrid(l, state) {
            var res = "";
            for (var i = 0; i < l.length; i++) {
                var h = l[i];
                if (!h.Caption) continue;
                var showInList = true;
                var hidden = h.Hidden;
                for (var j in this.columns) {
                    var c = this.columns[j];
                    if (c.Name == h.Name) {
                        showInList = c.ShowInList;
                        hidden = c.Hidden;
                        break;
                    }
                }
                if (!showInList) continue;
                h.Hidden = hidden;
                h.HiddenDefault = h.HiddenDefault != null ? h.HiddenDefault : h.Hidden;
                res += '<li class="grid-tree-node' + (i == l.length - 1 ? ' last' : '') + (h.Children.length == 0 ? ' leaf' : ' closed') + '">' +
                    '<div class="grid-tree-expand"></div><div class="grid-tree-content"><a href="#">' +
                    '<div class="grid-tree-check' + (hidden ? '' : ' checked') + '" data-id="' + globalHeaderId + '"></div>' + h.Caption + '</a></div>';
                headerDictionary[globalHeaderId] = h;
                globalHeaderId++;
                if (h.Children.length > 0)
                    res += '<ul class="grid-tree-ul">' + addUlGrid(h.Children, false) + '</ul>';
                res += '</li>';
            }
            return res;
        }
    },
    createTable: function (data) {
         var totalWidth = 0;
        var cols = "";
        for (var i = 0; i < this.columns.length; i++) {
            var c = this.columns[i];
            if (c.Hidden) continue;
            var w = c.Width || 100;
            totalWidth += w;
            cols += "<col width='" + w + "' style='width:" + w + "px'/>";
        }
        cols += "<col width='" + 0 + "' style='width:0px'>";
        this.lastWidth = 0;
        var colGroup = "<colgroup class='grid-header-colgroup'>" + cols + "</colgroup>";
        var thead = "<thead>";
        for (var i = 0; i < this.header.length; i++) {
            var tr = "";
            var pos = 0;
            for (var j = 0; j < this.header[i].length; j++) {
                var c = this.header[i][j];

                var prop = " title='" + (c.Tooltip || c.Caption).replace(/<(?:.|\n)*?>/gm, '') + "'";

                if (c.colSpan > 1)
                    prop += " colSpan='" + c.colSpan + "'";
                if (c.rowSpan > 1)
                    prop += " rowSpan='" + c.rowSpan + "'";

                var pos = -1;
                var kk = 0;
                for (var k = 0; k < this.columns.length; k++) {
                    var c1 = this.columns[k];
                    if (c1.Name == c.Name) {
                        pos = kk;
                        break;
                    }
                    if (!c1.Hidden) kk++;
                }

                //use a nested table so that the resizer is on the right without addition table have defects in some browsers (ie, firefox)
                var resize = pos == -1 ? "" : "<td class='grid-resize' position='" + pos + "'></td>";
                tr += "<th" + prop + "><table class='grid-header-inner-table'><tr><td class='grid-sort'>" + c.Caption + "</td>" + resize + "</tr></table></th>";
                pos += 1;
            }
            tr += "<th class='grid-fake-column'>&nbsp;</th>";
            thead += "\n<tr>" + tr + "</tr>";
        }
        thead += "</thead>";
        var table = "<table class='grid-header-table' style='width:" + totalWidth + "px'>" + colGroup + thead + "</table>";
        var div = "<div class='grid-header'>" + table + "</div>";
        this.$mainDiv.append(div);

        //created dom-elements
        this.$headerDiv = this._find('.grid-header', this.$mainDiv);
        this.$headerTable = this._find('.grid-header-table', this.$headerDiv);
        this.$headerColgroup = this._find('.grid-header-colgroup', this.$headerTable);
        this.$headerThead = this._find('thead', this.$headerTable);
        this.$resizer = $('.grid-resize', this.$headerTable);

        this.updateResizersHeight();

        cols = "";
        for (i = 0; i < this.columns.length; i++) {
            c = this.columns[i];
            if (c.Hidden)
                continue;
            w = c.Width || 100;
            cols += "<col width='" + w + "' style='width:" + w + "px'/>";
        }
        colGroup = "<colgroup class='grid-data-colgroup'>" + cols + "</colgroup>";

        var content = this.createContent(data, 1, "top");
        var tbody = "<tbody>" + content + "</tbody>";
        table = "<table class='grid-data-table' style='width:" + totalWidth + "px'>" + colGroup + tbody + "</table>";
        div = "<div class='grid-data'>" + table + "</div>";
        this.$mainDiv.append(div);
        var resizer = "<div class='grid-resize-ghost'></div>";
        this.$mainDiv.append(resizer);
        var resizerCol1 = "<div class='grid-resize-ghost-col1'></div>";
        var resizerCol2 = "<div class='grid-resize-ghost-col2'></div>";
        this.$mainDiv.append(resizerCol1).append(resizerCol2);

        this.$dataDiv = this._find('.grid-data', this.$mainDiv);
        this.$dataTable = this._find('.grid-data-table', this.$dataDiv);
        this.$dataColgroup = this._find('.grid-data-colgroup', this.$dataTable);
        this.$dataTbody = this._find('tbody', this.$dataTable);
        this.$resizeGhost = this._find('.grid-resize-ghost', this.$mainDiv);
        this.$resizeGhostCol1 = this._find('.grid-resize-ghost-col1', this.$mainDiv);
        this.$resizeGhostCol2 = this._find('.grid-resize-ghost-col2', this.$mainDiv);

        this._resize();
    },
    groupClick: function (e) {
        var $div = $(e.target);
        this.doGroupClick($div);
    },
    doGroupClick: function ($div, ignoreWait) {
        if (!$div.is('.grid-plus, .grid-minus'))
            return false;
        if (ignoreWait != true && $(this.$mainDiv).css('cursor') == 'wait')
            return false;
        var $tr = $div.parent().parent();
        var id = $tr.attr('rowid');
        var parentId = $tr.attr('parentId');
        var parentStr = $.trim(id + " " + parentId);
        var $children = this.$dataTable.find('tr[parentId~="' + id + '"]');
        var $children1, $children2;
        if ($div.hasClass('grid-plus') && $children.length == 0) {
            var level = parseInt($tr.attr('level')) + 1;
            var params = $.extend({}, this.params, { g_parentId: id, g_level: level, d_logId: this.logId });
            var obj = this;
            $div.removeClass('grid-plus').addClass('grid-wait');

            var params = $.extend({}, this.params, { parentId: id });
            $.ajax({ type: this.opt.method || 'POST', cache: false, url: this.opt.url, data: params})
            .done(function (data) {
                $div.removeClass('grid-wait').addClass('grid-minus');

                var content = obj.createContent(data, level, parentStr);
                var $content = $(content);
                $content.insertAfter($tr);
                obj._resize();
            }).fail(function () {
                obj.ajax_error(arguments);
            });
        }
        else if ($div.hasClass('grid-plus')) {
            $children1 = this.$dataTable.find('tr[parentId^="' + id + ' "]');
            $children2 = this.$dataTable.find('tr[parentId~="' + id + '"]:not(.grid-tr-closed)');
            $children1.show().removeClass('grid-tr-closed');
            $children2.show();
            $div.removeClass('grid-plus').addClass('grid-minus');
            this._resize();
        }
        else {
            $children1 = this.$dataTable.find('tr[parentId^="' + id + ' "]');
            $children2 = this.$dataTable.find('tr[parentId~="' + id + '"]:not(.grid-tr-closed)');
            $children1.hide().addClass('grid-tr-closed');
            $children2.hide();
            $div.removeClass('grid-minus').addClass('grid-plus');
            this._resize();
        }

        return false;
    },
    rowClick: function (tr) {
        if ($(tr).hasClass('grid-info-row'))
            return;
        this.$dataDiv.find('tr.grid-active-row').removeClass('grid-active-row');
        $(tr).addClass('grid-active-row');
        this.activeRowId = $(tr).attr('rowid');
    },
    //generate colspan, rowspan for nested columns
    headerTable: function (header, columns) {
        var l = [];
        for (var i = 0; i < header.length; i++) {
            var h = header[i];
            if (h.Hidden) continue;
            l.push(header[i]);
        }
        var ls = [];
        while (l.length > 0) {
            var nl = [];
            for (var i = 0; i < l.length; i++) {
                var h = l[i];
                delete h.colSpan;
                for (var j = 0; j < h.Children.length; j++) {
                    var h1 = h.Children[j];
                    if (h1.Hidden) continue;
                    nl.push(h1);
                    h1.parent = h;
                }
            }
            ls.push(l);
            l = nl;
        }
        var visibleColumns = {};
        for (var i = ls.length - 1; i >= 0; i--) {
            if (ls[i].length == 0) {
                delete ls[i];
                continue;
            }
            for (var j = 0; j < ls[i].length; j++) {
                var lsij = ls[i][j];
                var p = lsij.parent;
                if (!lsij.colSpan) lsij.colSpan = 1;
                if (p) p.colSpan = p.colSpan ? p.colSpan + lsij.colSpan : lsij.colSpan;
            }
        }
        for (var i = 0; i < ls.length; i++) {
            for (var j = 0; j < ls[i].length; j++) {
                var lsij = ls[i][j];
                lsij.rowSpan = lsij.Children.length > 0 ? 1 : ls.length - i;
                if (lsij.Name) {
                    columns.push(lsij);
                    visibleColumns[lsij.Name] = true;
                }
            }
        }

        for (var i = 0; i < columns.length; i++) {
            if (!visibleColumns[columns[i].Name]) columns[i].Hidden = true;
        }

        return ls;
    },
    //insert table data
    createContent: function (data, level, parentStr) {
        var rows = data.Data.Rows;
        this.columnPos = [];
        for (var i = 0; i < this.columns.length; i++) {
            var pos = null;
            for (var j = 0; j < data.Data.Schema.length; j++) {
                if (this.columns[i].Name.toLowerCase() == data.Data.Schema[j].toLowerCase()) {
                    pos = j;
                    break;
                }
            }
            this.columnPos.push(pos);
        }

        var idPos = -1;
        for (var j = 0; j < data.Data.Schema.length; j++) {
            if (data.Key && data.Data.Schema[j].toLowerCase() == data.Key.toLowerCase()) {
                idPos = j;
                break;
            }
        }
        var isFolderPos = -1;
        for (var j = 0; j < data.Data.Schema.length; j++) {
            if (data.Key && data.Data.Schema[j].toLowerCase() == "isfolder") {
                isFolderPos = j;
                break;
            }
        }

        var content = "";
        for (var i = 0; i < rows.length; i++) {
            var r = rows[i];
            var id = idPos != -1 ? r[idPos] : '';
            var isFolder = isFolderPos != -1 ? r[isFolderPos] : false;

            var plus = isFolder ? " grid-plus" : "";
            var row = "";
            for (var j = 0; j < this.columns.length; j++) {
                var cellData = this.columnPos[j] != null ? r[this.columnPos[j]] : '';
                var text = cellData;
                var cl = "";
                var c = this.columns[j];
                if (c.Type == 'number') {
                    text = this.format(cellData, c.Precision, '.', ',');
                    if (!c.Align)
                        c.Align = 'right';
                }
                else if (c.Type == 'percent') {
                    text = this.format(parseFloat(cellData) * 100, c.Precision, '.', ',') + '%';
                    if (!c.Align)
                        c.Align = 'right';
                }
                else if (c.Type == 'bool') {
                    var b = this.parseBool(cellData);
                    text = '<span class="grid-tree-check' + (b ? ' checked' : (b == null ? ' null' : '')) + ' grid-checkbox"></span>';
                }

                if (c.Align) {
                    if (cl.length > 0)
                        cl += " ";
                    cl += c.Align;
                }
                if (i == 0) {
                    if (cl.length > 0)
                        cl += " ";
                    cl += "first";
                }
                if (cl.length > 0)
                    cl = " class='" + cl + "'";

                if (j == 0) {
                    var padding = level * 10 + "px";
                    var groupStr = "";
                    if (isFolder)
                        groupStr = "<span class='grid-group" + plus + "'></span>";
                    row += "<td" + cl + " style='padding-left:" + padding + "'>" + groupStr + text + "</td>";
                }
                else {
                    row += '<td' + cl + ' >' + text + "</td>";
                }
            }

            content += "<tr class='grid-level-" + level + "' level='" + level + "' rowid='" + id + "' parentId='" + parentStr + "'>" + row + "</tr>";
        }
        return content;
    },
    bindEvents: function (data) {
        this.resizeInfo = this.resizeInfoSize = this.resizeInfoCol = null;
        var obj = this;

        //sorting and drag-and-drop columns
        this.$headerTable.find('.grid-sort').each(function () {
            if (obj.opt.sort) {
                $(this).click(function () {
                    var colPos = $(this).next().attr('position');
                    obj.sort(colPos);
                    return false;
                });
            }

            if (obj.opt.dad_col) {
                $(this).on('mousedown', function (e) {
                    var $resize = $(this).parent().find('.grid-resize');
                    var colPos = parseInt($resize.attr('position'));
                    obj.dragStartCol(colPos, e, $resize, data.ExpandFirstLevel);
                    return false;
                });
            }
        });

        if (this.opt.resize_tab) {
            this.$mainDiv.append('<div class="grid-resizer"></div>');
            $('.grid-resizer', this.$mainDiv).mousedown(function (e) {
                obj.dragStartSize(e);
            });
        }

        //change table size
        if (this.opt.resize_col) {
            this.$resizer.each(function (i) {
                $(this).mousedown(function (e) {
                    var colPos = parseInt($(this).attr('position'));
                    obj.dragStart(colPos, e, $(this));
                    return false;
                });
            });
        }
        else {
            this.$resizer.each(function (i) {
                $(this).css('cursor', 'auto');
            });
        }

        this.$mainDiv.mousemove(function (e) {
            if (obj.resizeInfo) {
                obj.dragMove(e);
                return false;
            }
            else if (obj.resizeInfoCol) {
                obj.dragMoveCol(e);
                return false;
            }
            return true;
        }).mouseup(function (e) {
            if (obj.resizeInfo) {
                obj.dragEnd();
                return false;
            }
            else if (obj.resizeInfoCol) {
                var colPos;
                if ($(e.target).hasClass('grid-sort'))
                    colPos = parseInt($(e.target).parent().find('.grid-resize').attr('position'));
                obj.dragEndCol(colPos, data);
                return false;
            }
            return true;
        });

        $(document).off("mousemove", mouseMove).on("mousemove", mouseMove);

        function mouseMove(e) {
            if (e.button != 1 && e.buttons != 1)
                obj.resizeInfoSize = null;

            if (obj.resizeInfoSize)
                obj.dragMoveSize(e);

            return true;
        }

        //expand/collapse tree
        this.$dataDiv.on('click', '.grid-group', function (e) { obj.groupClick(e); });

        //click on row
        this.$dataDiv.on('click', 'tr', function (e) { obj.rowClick(this); });

        //scroll
        this.$dataDiv.scroll(function () {
            obj.$headerDiv.scrollLeft(obj.$dataDiv.scrollLeft());
        });
    },
    parseBool: function (val) {
        if ((typeof val === 'string' && (val.toLowerCase() === 'true' || val.toLowerCase() === 'yes' || val === '1')) || val === 1 || (typeof val === 'boolean' && val))
            return true;
        else if ((typeof val === 'string' && (val.toLowerCase() === 'false' || val.toLowerCase() === 'no' || val === '0')) || val === 0 || (typeof val === 'boolean' && !val))
            return false;

        return null;
    },
    format: function (n, decimals, decimal_sep, thousands_sep) {
        var c = isNaN(decimals) ? 2 : Math.abs(decimals),
            d = decimal_sep || '.',
            t = (typeof thousands_sep === 'undefined') ? ',' : thousands_sep,
            sign = (n < 0) ? '-' : '',
            i = parseInt(n = Math.abs(n).toFixed(c)) + '',
            j = ((j = i.length) > 3) ? j % 3 : 0;
        return sign + (j ? i.substr(0, j) + t : '') + i.substr(j).replace(/(\d{3})(?=\d)/g, "$1" + t) + (c ? d + Math.abs(n - i).toFixed(c).slice(2) : '');
    },
    sort: function (i) {
        var column = this.columns[i];
        if (!column)
            return;

        var asc = true;
        if (this.opt.sort_num_desc && (column.Type == "number" || column.Type == "percent"))
            asc = false;
        var $col = this.$headerDiv.find('.grid-resize[position=' + i + ']').last().prev();
        if ($col.find('span.grid-sort-asc').length > 0)
            asc = false;
        else if ($col.find('span.grid-sort-desc').length > 0)
            asc = true;

        var orderBy = column.Name + (asc ? "" : " desc");
        this.init(orderBy);
    },
    showSort: function (i, asc) {
        var $col = this.$headerDiv.find('.grid-resize[position=' + i + ']').last().prev();
        this.$headerTable.find('span.grid-sort-asc, span.grid-sort-desc').remove();
        var span = '<span class="' + (asc ? 'grid-sort-asc' : 'grid-sort-desc') + '"></span>';
        $col.append(span);
        return asc;
    },
    dragStart: function (i, x, handler) {
        this.resizeInfo = {
            id: i,
            handler: handler,
            startX: x.clientX,
            offset: this.getOffset(i, handler)
        };
        this.$resizeGhost.css({
            display: 'block',
            height: this.$mainDiv.height() + 2 + 'px',
            left: this.resizeInfo.offset + 'px',
            cursor: 'col-resize'
        });
        var $cell = $('col', this.$headerColgroup);
        this.resizeInfo.newWidth = this.resizeInfo.oldWidth = parseInt($cell.eq(this.resizeInfo.id).width());
    },
    dragMove: function (x) {
        var diff = x.clientX - this.resizeInfo.startX;
        this.resizeInfo.newWidth = this.resizeInfo.oldWidth + diff;
        if (this.resizeInfo.newWidth > parseInt(30)) {
            this.$resizeGhost.css({
                left: this.resizeInfo.offset + diff + 'px'
            });
        }
        else {
            this.resizeInfo.newWidth = parseInt(30);
        }
    },
    dragEnd: function () {
        var newWidth = this.resizeInfo.newWidth + 'px';
        var pos = this.resizeInfo.id;
        var $headerCol = this.$headerColgroup.find('col').eq(pos);
        $headerCol.css({ width: newWidth });
        $headerCol.attr('width', this.resizeInfo.newWidth);
        var $dataCol = this.$dataColgroup.find('col').eq(pos);
        $dataCol.css({ width: newWidth });
        $dataCol.attr('width', this.resizeInfo.newWidth);

        var diff = this.resizeInfo.newWidth - this.resizeInfo.oldWidth;
        var widthTotalHeader = this.$headerTable.width();
        var widthTotalData = this.$dataTable.width();
        this.$headerTable.width(widthTotalHeader + diff);
        this.$dataTable.width(widthTotalData + diff);

        this._resize();

        this.resizeInfo = null;
        this.$resizeGhost.css({
            display: 'none'
        });
    },
    getOffset: function (col, handler) {
        var ret = 0;
        var cell = $('col', this.$headerColgroup);
        var bso = this.$dataDiv.scrollLeft();
        for (var i = 0; i < col; i++) {
            ret += parseInt(cell.eq(i).width());
        }
        var offset = handler[0].offsetLeft + 5 + ret - bso;
        return offset;
    },
    dragStartCol: function (i, x, handler, expandFirstLevel) {
        if (isNaN(i))
            return;

        if (i == 0) {
            if (this.$dataTable.find('.grid-group:first').length > 0)
                return;
            if (expandFirstLevel)
                return;
        }

        this.resizeInfoCol = {
            id: i,
            handler: handler,
            startX: x.clientX,
            offset: this.getOffsetCol(i, handler)
        };
        var $cell = $('col', this.$headerColgroup);
        this.resizeInfoCol.newWidth = this.resizeInfoCol.oldWidth = parseInt($cell.eq(this.resizeInfoCol.id).width());
        this.$resizeGhostCol1.css({
            display: 'block',
            height: this.$mainDiv.height() + 2 + 'px',
            left: this.resizeInfoCol.offset + 'px'
        });
        this.$resizeGhostCol2.css({
            display: 'block',
            height: this.$mainDiv.height() + 2 + 'px',
            left: this.resizeInfoCol.offset + this.resizeInfoCol.oldWidth - 2 + 'px'
        });
    },
    dragMoveCol: function (x) {
        var diff = x.clientX - this.resizeInfoCol.startX;
        this.resizeInfoCol.newWidth = this.resizeInfoCol.oldWidth + diff;
        this.$resizeGhostCol1.css({
            left: this.resizeInfoCol.offset + diff + 'px'
        });
        this.$resizeGhostCol2.css({
            left: this.resizeInfoCol.offset + this.resizeInfoCol.oldWidth - 2 + diff + 'px'
        });
    },
    dragEndCol: function (newPos, data) {
        var newWidth = this.resizeInfoCol.newWidth + 'px';
        var pos = this.resizeInfoCol.id;
        var $headerCol = this.$headerColgroup.find('col').eq(pos);

        this.$resizeGhostCol1.css({
            display: 'none'
        });
        this.$resizeGhostCol2.css({
            display: 'none'
        });

        var i1 = this.resizeInfoCol.id;
        var i2 = newPos;
        if (i2 == null || isNaN(i2) || i1 == i2)
            return;
        var name1 = this.columns[i1].Name;
        var name2 = this.columns[i2].Name;
        this.resizeInfoCol = null;

        var hip1 = this.findHIP(data.Columns, name1);
        var hip2 = this.findHIP(data.Columns, name2);
        if (!hip1 || !hip2)
            return;
        if (hip1.parent != hip2.parent)
            return;

        this.columnPosition = [[name1, name2]];

        this.fillData(data);
    },
    getOffsetCol: function (col, handler) {
        var ret = 0;
        var cell = $('col', this.$headerColgroup);
        var bso = this.$dataDiv.scrollLeft();
        for (var i = 0; i < col; i++) {
            ret += parseInt(cell.eq(i).width());
        }
        var offset = ret - bso;
        return offset;
    },
    dragStartSize: function (x) {
        this.resizeInfoSize = {
            startX: x.clientX,
            startY: x.clientY
        };
    },
    dragMoveSize: function (x) {
        var diffX = x.clientX - this.resizeInfoSize.startX;
        var diffY = x.clientY - this.resizeInfoSize.startY;
        this.resizeInfoSize.startX = x.clientX;
        this.resizeInfoSize.startY = x.clientY;
        this.$mainDiv.width(this.$mainDiv.width() + diffX).height(this.$mainDiv.height() + diffY);
        this._resize();
    },
    dragEndSize: function () {
        this.resizeInfoSize = null;
    },
    changeColumns: function (data) {
        if (!this.columnPosition || this.columnPosition.length == 0)
            return;

        for (var i = 0; i < this.columnPosition.length; i++) {
            var cp = this.columnPosition[i];

            //header
            var hip1 = this.findHIP(data.Columns, cp[0]);
            var hip2 = this.findHIP(data.Columns, cp[1]);
            if (!hip1 || !hip2)
                continue;

            var tmp = hip1.parent[hip1.pos];
            hip1.parent.splice(hip1.pos, 1);
            hip2.parent.splice(hip2.pos, 0, tmp);
        }
    },
    findHIP: function (header, name) {
        for (var i = 0; i < header.length; i++) {
            if (header[i].Name == name)
                return { parent: header, pos: i };
            for (var j = 0; j < header[i].Children.length; j++) {
                var hip = this.findHIP(header[i].Children, name);
                if (hip)
                    return hip;
            }
        }
        return null;
    },
    _resize: function () {
        if (this.$headerDiv == null)
            return;

        var width = Math.min(this.$mainDiv.width(), this.$headerTable.width() + 20);
        var height = this.$mainDiv.height();

        this.$headerDiv.width(width);
        this.$dataDiv.width(width);

        var dataHeight = height - this.$headerDiv.height();
        if (this.$toolbar)
            dataHeight -= this.$toolbar.height();
        if (dataHeight < 0)
            dataHeight = 0;
        this.$dataDiv.height(dataHeight);
        if (this.$headerDiv.height() > height)
            this.$headerDiv.hide();
        else
            this.$headerDiv.show();

        var lastWidth = 0;
        var $col;
        //change size for last fake column if both scrolls visible
        if (this.$dataDiv[0].clientHeight < this.$dataDiv[0].scrollHeight &&
            this.$dataDiv[0].clientWidth < this.$dataDiv[0].scrollWidth)
            lastWidth = 20;
        if (this.lastWidth != lastWidth) {
            var selector = 'col:nth-child(' + (this.columns.length + 1) + ')';
            $col = this.$headerColgroup.find(selector);
            $col.css({ width: lastWidth + 'px' });
            $col.attr('width', lastWidth);
            this.lastWidth = lastWidth;
        }

        //set table size
        var $colsHeader = this.$headerColgroup.find('col');
        var widthTotalHeader = 0;
        for (var i = 0; i < $colsHeader.length; i++)
            widthTotalHeader += parseInt($colsHeader.eq(i).attr('width'));
        var $colsData = this.$dataColgroup.find('col');
        var widthTotalData = 0;
        for (i = 0; i < $colsData.length; i++)
            widthTotalData += parseInt($colsData.eq(i).attr('width'));
        this.$headerTable.width(widthTotalHeader);
        this.$dataTable.width(widthTotalData);

        if (this.$toolbar) {
            this.$toolbar.width(Math.min(width, widthTotalData + 1));
        }
    },
    updateResizersHeight: function () {
        this.$headerTable.find('th').each(function () {
            $(this).find('table').height($(this).height());
        });
    },
    _find: function (selector, parent) {
        var res = $(selector, parent);
        if (res.length == 0)
            throw "Not found element '" + selector + "' inside '" + parent[0].tagName + "'";
        if (res.length > 1)
            throw "Found more than 1 element '" + selector + "' inside '" + parent[0].tagName + "'";

        return res;
    }
}
