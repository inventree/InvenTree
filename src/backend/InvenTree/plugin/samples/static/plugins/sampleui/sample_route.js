export function getBasicPage(_context) {
    return React.createElement(
        'div',
        { style: { padding: 24 } },
        React.createElement('h1', null, 'Sample Plugin Route'),
        React.createElement('p', null, 'Plugin route is working.')
    );
}

export function getArgPage(_context) {
    const arg1 = window.location.pathname.split('/').pop();

    return React.createElement(
        'div',
        { style: { padding: 24 } },
        React.createElement('h1', null, 'Sample Plugin Route'),
        React.createElement('p', null, 'Plugin route is working.'),
        React.createElement('p', null, `Arg 1: ${arg1}.`)
    );
}
