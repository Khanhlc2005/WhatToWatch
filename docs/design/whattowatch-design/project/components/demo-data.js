/* Sample data for previews only. `art` stands in for TMDB poster images, which previews cannot load. */
window.WTW_DEMO = (function () {
  var m = [
    { id: '278', title: 'The Shawshank Redemption', year: 1994, rating: 9.3, runtime: 142, art: ['#1f3b3a', '#e8d9b5'], genres: ['Drama', 'Crime'], cast: 'Tim Robbins, Morgan Freeman, Bob Gunton', overview: 'Imprisoned in the 1940s for the double murder of his wife and her lover, upstanding banker Andy Dufresne begins a new life at the Shawshank prison.' },
    { id: '238', title: 'The Godfather', year: 1972, rating: 9.2, runtime: 175, art: ['#4a1c1c', '#f0c9a0'], genres: ['Drama', 'Crime'], cast: 'Marlon Brando, Al Pacino, James Caan', overview: 'Spanning the years 1945 to 1955, a chronicle of the fictional Italian-American Corleone crime family.' },
    { id: '129', title: 'Spirited Away', year: 2001, rating: 8.6, runtime: 125, art: ['#c9a227', '#1c1a14'], genres: ['Animation', 'Family', 'Fantasy'], cast: 'Rumi Hiiragi, Miyu Irino, Mari Natsuki', overview: 'A young girl, Chihiro, becomes trapped in a strange new world of spirits.' },
    { id: '496243', title: 'Parasite', year: 2019, rating: 8.5, runtime: 133, art: ['#2f3a4a', '#d7dde6'], genres: ['Comedy', 'Thriller', 'Drama'], cast: 'Song Kang-ho, Lee Sun-kyun, Cho Yeo-jeong', overview: 'All unemployed, Ki-taek’s family takes peculiar interest in the wealthy and glamorous Parks.' },
    { id: '157336', title: 'Interstellar', year: 2014, rating: 8.7, runtime: 169, art: ['#1d2540', '#f2b8a2'], genres: ['Adventure', 'Drama', 'Science Fiction'], cast: 'Matthew McConaughey, Anne Hathaway, Jessica Chastain', overview: 'A group of explorers make use of a newly discovered wormhole to surpass the limitations on human space travel.' },
    { id: '244786', title: 'Whiplash', year: 2014, rating: 8.5, runtime: 107, art: ['#8a3b1d', '#f6e6d2'], genres: ['Drama', 'Music'], cast: 'Miles Teller, J.K. Simmons, Melissa Benoist', overview: 'Under the direction of a ruthless instructor, a talented young drummer begins to pursue perfection at any cost.' },
    { id: '843', title: 'In the Mood for Love', year: 2000, rating: 8.1, runtime: 98, art: ['#3a2440', '#e7cfe0'], genres: ['Drama', 'Romance'], cast: 'Tony Leung Chiu-wai, Maggie Cheung', overview: 'In 1962 Hong Kong, two neighbours form a bond after both suspect their spouses of extra-marital activities.' },
    { id: '329865', title: 'Arrival', year: 2016, rating: 7.9, runtime: 116, art: ['#e8dcc4', '#2a211a'], genres: ['Drama', 'Science Fiction', 'Mystery'], cast: 'Amy Adams, Jeremy Renner, Forest Whitaker', overview: 'Taking place after alien crafts land around the world, an expert linguist is recruited by the military to determine whether they come in peace.' },
    { id: '76341', title: 'Mad Max: Fury Road', year: 2015, rating: 8.1, runtime: 121, art: ['#b4541f', '#1a120c'], genres: ['Action', 'Adventure', 'Science Fiction'], cast: 'Tom Hardy, Charlize Theron, Nicholas Hoult', overview: 'An apocalyptic story set in the furthest reaches of our planet, in a stark desert landscape.' },
    { id: '666277', title: 'Past Lives', year: 2023, rating: 7.8, runtime: 106, art: ['#20352a', '#c8e0b8'], genres: ['Drama', 'Romance'], cast: 'Greta Lee, Teo Yoo, John Magaro', overview: 'Nora and Hae Sung, two childhood friends, are reunited in New York for one fateful week.' },
    { id: '999001', title: 'An Untitled Restoration', year: 1958, rating: null, art: null, genres: [], overview: '' }
  ];
  return {
    movies: m,
    reasons: ['Matches your taste · Highly rated on IMDb', 'Matches your taste', 'Highly rated on IMDb', 'Matches your taste · Highly rated on IMDb', 'Matches your taste', 'Highly rated on IMDb', 'Matches your taste', 'Recommended for you'],
    genres: [
      { id: 28, name: 'Action' }, { id: 12, name: 'Adventure' }, { id: 16, name: 'Animation' }, { id: 35, name: 'Comedy' }, { id: 80, name: 'Crime' },
      { id: 99, name: 'Documentary' }, { id: 18, name: 'Drama' }, { id: 10751, name: 'Family' }, { id: 14, name: 'Fantasy' }, { id: 36, name: 'History' },
      { id: 27, name: 'Horror' }, { id: 10402, name: 'Music' }, { id: 9648, name: 'Mystery' }, { id: 10749, name: 'Romance' }, { id: 878, name: 'Science Fiction' },
      { id: 10770, name: 'TV Movie' }, { id: 53, name: 'Thriller' }, { id: 10752, name: 'War' }, { id: 37, name: 'Western' }
    ],
    conversations: [
      { id: 3, title: 'Slow sci-fi for a rainy night', when: '2H AGO' },
      { id: 2, title: 'Korean thrillers like Parasite', when: 'YESTERDAY' },
      { id: 1, title: 'Something short and funny', when: 'OCT 19' }
    ]
  };
})();
