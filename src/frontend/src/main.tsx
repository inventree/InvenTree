import React from 'react';
import ReactDOM from 'react-dom/client';

import App from './App';

ReactDOM.createRoot(document.getElementById('root') as HTMLElement).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);

// Redirect to /platform if on / - while building for netlify
console.log(process.env.NETLIFY_PREVIEW);
console.log(process.env);
if (process.env.NETLIFY_PREVIEW == 'TRUE') {
  if (window.location.pathname === '/') {
    window.location.replace('/platform');
  }
}
