
export default {
  bootstrap: () => import('./main.server.mjs').then(m => m.default),
  inlineCriticalCss: true,
  baseHref: '/',
  locale: undefined,
  routes: undefined,
  entryPointToBrowserMapping: {},
  assets: {
    'index.csr.html': {size: 494, hash: '9d4e0b0e68be57232fdbae4fdefcb765b789252107804a41f30c09934fe50d12', text: () => import('./assets-chunks/index_csr_html.mjs').then(m => m.default)},
    'index.server.html': {size: 1007, hash: '787c95ca5ae8fcf6b8ef9621856b8efb9dc46ae530a929bd4d230ad6a1ef628e', text: () => import('./assets-chunks/index_server_html.mjs').then(m => m.default)},
    'styles-5INURTSO.css': {size: 0, hash: 'menYUTfbRu8', text: () => import('./assets-chunks/styles-5INURTSO_css.mjs').then(m => m.default)}
  },
};
