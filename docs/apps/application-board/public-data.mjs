import {loadPublicDataset} from './public-data-loader.mjs';
// Node/offline catalogue tests read the reviewed bundled release. The browser
// always revalidates JSON; a network failure must not silently show old data.
export const publicReleaseDataset=typeof document==='undefined'
 ? (await import('./public-dataset.mjs')).publicReleaseDataset
 : await loadPublicDataset(new URL('./public-dataset.json',import.meta.url));
