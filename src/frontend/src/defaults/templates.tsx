export const defaultLabelTemplate = `{% extends "label/label_base.html" %}

{% load l10n i18n barcode %}

{% block style %}

.qr {
    position: absolute;
    left: 0mm;
    top: 0mm;
    {% localize off %}
    height: {{ height }}mm;
    width: {{ height }}mm;
    {% endlocalize %}
}

{% endblock style %}

{% block content %}
<img class='qr' alt="{% trans 'QR Code' %}" src='{% qrcode qr_data %}'>

{% endblock content %}
`;

export const defaultReportTemplate = `{% extends "report/inventree_report_base.html" %}

{% load i18n report barcode inventree_extras %}

{% block page_margin %}
margin: 2cm;
margin-top: 4cm;
{% endblock page_margin %}

{% block bottom_left %}
content: "v{{ report_revision }} - {{ date.isoformat }}";
{% endblock bottom_left %}

{% block bottom_center %}
content: "{% inventree_version shortstring=True %}";
{% endblock bottom_center %}

{% block style %}
<!-- Custom style -->
{% endblock style %}

{% block header_content %}
<!-- Custom header content -->
{% endblock header_content %}

{% block page_content %}
<!-- Custom page content -->
{% endblock page_content %}
`;
