const assert = require('assert').strict;
const fs = require('fs');
const ts = require('typescript');
const vm = require('vm');
const path = require('path');
const compiled = ts.transpileModule(fs.readFileSync(path.join(__dirname, '../lib/movies.ts'), 'utf8'), {
  compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2019 }
});
const sandbox = { exports: {} };
vm.runInNewContext(compiled.outputText, sandbox);
const { toMovie } = sandbox.exports;
const summary = { id: 7, title: 'Fixture', posterUrl: '/poster.jpg', voteAverage: 8.2, releaseDate: '2000-01-01' };
assert.equal(toMovie(summary).id, '7');
assert.equal(toMovie(summary).rating, 8.2);
assert.equal(toMovie(summary).poster, 'https://image.tmdb.org/t/p/w500/poster.jpg');
assert.equal(toMovie({ ...summary, voteAverage: null }).rating, null);
assert.equal(toMovie(summary).trailerKey, undefined);
const detail = { id: 7, title: 'Fixture', overview: 'Overview', posterPath: null, backdropPath: null,
  tmdbVoteAverage: 0, imdbRating: 7.5, runtimeMinutes: 110, trailerKey: 'abc', trailerSite: 'YouTube', releaseDate: null };
assert.equal(toMovie(detail).id, toMovie(summary).id);
assert.equal(toMovie(detail).rating, 7.5);
assert.equal(toMovie(detail).runtime, 110);
assert.equal(toMovie(detail).trailerKey, 'abc');
assert.equal(toMovie({ ...detail, trailerSite: 'Vimeo' }).trailerKey, null);
assert.equal(toMovie(detail).genre.length, 0);
for (const id of [null, 0, -1, 1.5, 'uuid', '7', Number.MAX_SAFE_INTEGER + 1]) {
  assert.throws(() => toMovie({ ...summary, id }), /Invalid movie ID/);
}
console.log('Movie contract: PASS (summary/detail identity, ratings, nulls, trailers, unsafe IDs)');

async function testRoutes() {
  for (const route of ['index', 'trailer']) {
    const calls = [];
    const code = ts.transpileModule(fs.readFileSync(path.join(__dirname, `../pages/api/movies/[id]/${route}.ts`), 'utf8'), {
      compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2019 }
    });
    const context = { exports: {}, require(name) {
      if (name.endsWith('/lib/backend')) return { backendRequest: async path => { calls.push(path); return { id: 7 }; } };
      if (name.endsWith('/lib/api')) return { allowMethod: () => true, sendError: (_, error) => { throw error; } };
      throw new Error('Unexpected dependency: ' + name);
    } };
    vm.runInNewContext(code.outputText, context);
    const invoke = async id => {
      const response = { status(code) { this.code = code; return this; }, json(body) { this.body = body; } };
      await context.exports.default({ method: 'GET', query: { id } }, response);
      return response;
    };
    assert.equal((await invoke('7')).code, 200);
    assert.equal(calls[0], '/movies/7' + (route === 'trailer' ? '/trailer' : ''));
    for (const id of ['uuid', '12345678-1234-1234-1234-123456789abc', '0', '-1', '1.5', '9007199254740992', ['7']]) {
      assert.equal((await invoke(id)).code, 400);
    }
    assert.equal(calls.length, 1);
  }
  console.log('Movie API routes: PASS (numeric IDs forwarded; UUID/unsafe IDs rejected)');
}
testRoutes().catch(error => { console.error(error); process.exitCode = 1; });
