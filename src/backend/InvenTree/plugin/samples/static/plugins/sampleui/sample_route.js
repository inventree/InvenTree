export function getBasicPage(_context) {
    return React.createElement(
        'div',
        { style: { padding: 24 } },
        React.createElement('h1', null, 'Sample Plugin Route'),
        React.createElement('p', null, 'This page has been dynamically rendered by the plugin system.')
    );
}

export function getArgPage(_context) {
    const arg1 = window.location.pathname.split('/').pop();

    return React.createElement(
        'div',
        { style: { padding: 24 } },
        React.createElement('h1', null, 'Sample Plugin Route'),
        React.createElement('p', null, 'This page has been dynamically rendered by the plugin system.'),
        React.createElement('p', null, `Arg 1: ${arg1}.`)
    );
}
