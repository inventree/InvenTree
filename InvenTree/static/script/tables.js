function editButton(url, text='Edit') {
    return "<button class='btn btn-success edit-button btn-sm' type='button' url='" + url + "'>" + text + "</button>";
}

function deleteButton(url, text='Delete') {
    return "<button class='btn btn-danger delete-button btn-sm' type='button' url='" + url + "'>" + text + "</button>";
}

function renderLink(text, url) {
    if (text === '' || url === '') {
        return text;
    }

    return '<a href="' + url + '">' + text + '</a>';
}



