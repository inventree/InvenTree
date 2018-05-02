function renderLink(text, url) {
    if (text && url) {
        return '<a href="' + url + '">' + text + '</a>';
    }
    else if (text) {
        return text;
    }
    else {
        return '';
    }
}



