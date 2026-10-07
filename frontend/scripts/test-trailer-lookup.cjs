const assert = require('assert').strict;
const fs = require('fs');
const path = require('path');
const ts = require('typescript');
const vm = require('vm');

const source = fs.readFileSync(path.join(__dirname, '../lib/trailerLookup.ts'), 'utf8');
const compiled = ts.transpileModule(source, {
  compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2019 }
});
const requests = [];
let tmdbResults = [];
let searchResults = [];
let videoResults = [];
const sandbox = {
  exports: {}, process: { env: { TMDB_KEY: 'tmdb-test', YOUTUBE_API_KEY: 'youtube-test' } },
  URL, AbortController, setTimeout, clearTimeout,
  console: { warn() {} },
  fetch: async input => {
    const url = new URL(input);
    requests.push(url);
    let body;
    if (url.hostname === 'api.themoviedb.org') body = { results: tmdbResults };
    else if (url.pathname.endsWith('/search')) body = { items: searchResults };
    else if (url.pathname.endsWith('/videos')) body = { items: videoResults };
    else throw new Error('Unexpected URL');
    return { ok: true, json: async () => body };
  }
};
vm.runInNewContext(compiled.outputText, sandbox);
const { resolveTrailer } = sandbox.exports;
const movie = (id, overrides = {}) => ({
  id, title: 'Interstellar', originalTitle: 'Interstellar', tmdbId: 157336,
  releaseDate: '2014-11-05', trailerKey: null, trailerSite: null, ...overrides
});

async function run() {
  assert.equal(await resolveTrailer(movie(1, { trailerKey: 'zSWdZVtXT7E', trailerSite: 'YouTube' })), 'zSWdZVtXT7E');
  assert.equal(requests.length, 0);

  tmdbResults = [
    { key: 'aaaaaaaaaaa', site: 'YouTube', type: 'Teaser', official: true },
    { key: 'bbbbbbbbbbb', site: 'YouTube', type: 'Trailer', official: false },
    { key: 'ccccccccccc', site: 'YouTube', type: 'Trailer', official: true }
  ];
  assert.equal(await resolveTrailer(movie(2)), 'ccccccccccc');
  assert.equal(requests.length, 1);
  assert.equal(await resolveTrailer(movie(2)), 'ccccccccccc');
  assert.equal(requests.length, 1, 'positive lookup should be cached');

  tmdbResults = [];
  searchResults = [
    { id: { videoId: 'ddddddddddd' }, snippet: { title: 'Interstellar 2014 fan edit trailer' } },
    { id: { videoId: 'eeeeeeeeeee' }, snippet: { title: 'Interstellar (2014) Official Trailer' } },
    { id: { videoId: 'fffffffffff' }, snippet: { title: 'Interstellar (2019) Official Trailer' } }
  ];
  videoResults = [{
    id: 'eeeeeeeeeee', snippet: { title: 'Interstellar (2014) Official Trailer' },
    status: { embeddable: true, privacyStatus: 'public' },
    contentDetails: { duration: 'PT2M30S' }
  }];
  assert.equal(await resolveTrailer(movie(3)), 'eeeeeeeeeee');
  assert.equal(requests.filter(url => url.pathname.endsWith('/search')).length, 1);
  assert.equal(requests.filter(url => url.hostname === 'www.googleapis.com' && url.pathname.endsWith('/videos')).length, 1);

  videoResults[0].status.embeddable = false;
  assert.equal(await resolveTrailer(movie(4)), null);
  const before = requests.length;
  assert.equal(await resolveTrailer(movie(4)), null);
  assert.equal(requests.length, before, 'negative lookup should be cached');
  console.log('Trailer lookup: PASS (stored, TMDB priority, YouTube validation, cache, no match)');
}
run().catch(error => { console.error(error); process.exitCode = 1; });
