package com.project.movie_recommendation.service;

import com.project.movie_recommendation.client.AiServiceClient;
import com.project.movie_recommendation.dto.ai.AiMovieSearchResponse;
import com.project.movie_recommendation.dto.request.MovieFilterRequest;
import com.project.movie_recommendation.dto.response.HomeFeedResponse;
import com.project.movie_recommendation.dto.response.MovieDetailResponse;
import com.project.movie_recommendation.dto.response.MovieSummaryResponse;
import com.project.movie_recommendation.dto.response.PageResponse;
import com.project.movie_recommendation.dto.response.RecommendationMovieResponse;
import com.project.movie_recommendation.dto.response.TrailerResponse;
import com.project.movie_recommendation.entity.Genre;
import com.project.movie_recommendation.entity.Movie;
import com.project.movie_recommendation.exception.AppException;
import com.project.movie_recommendation.exception.ErrorCode;
import com.project.movie_recommendation.mapper.MovieMapper;
import com.project.movie_recommendation.repository.MovieRepository;
import com.project.movie_recommendation.repository.specification.MovieSpecification;
import lombok.AccessLevel;
import lombok.RequiredArgsConstructor;
import lombok.experimental.FieldDefaults;
import org.springframework.cache.annotation.Cacheable;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.domain.Specification;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDate;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.stream.Collectors;

@Service
@RequiredArgsConstructor
@FieldDefaults(level = AccessLevel.PRIVATE, makeFinal = true)
public class MovieService {
    MovieRepository movieRepository;
    MovieMapper movieMapper;
    AiServiceClient aiServiceClient;

    private static final int HOME_FEED_GENRE_COUNT = 6;

    @Transactional(readOnly = true)
    public HomeFeedResponse getHomeFeed(RecommendationMovieResponse recommendation, int rowLimit) {
        String recStatus = recommendation != null && recommendation.status() != null
                ? recommendation.status()
                : "guest";

        List<MovieSummaryResponse> recommendedForYou = recommendation != null && recommendation.hits() != null
                ? recommendation.hits().stream()
                .map(RecommendationMovieResponse.Hit::movie)
                .filter(Objects::nonNull)
                .limit(rowLimit)
                .toList()
                : List.of();

        List<MovieSummaryResponse> topRated = getTopRatedMovies().stream()
                .limit(rowLimit)
                .toList();

        List<MovieSummaryResponse> newest = getNewestMovies().stream()
                .limit(rowLimit)
                .toList();

        List<Genre> popularGenres = movieRepository.findPopularGenres(PageRequest.of(0, HOME_FEED_GENRE_COUNT));
        List<HomeFeedResponse.GenreRowResponse> genreRows = popularGenres.stream()
                .map(genre -> {
                    List<MovieSummaryResponse> movies = movieRepository
                            .findTopMoviesByGenreId(genre.getId(), PageRequest.of(0, rowLimit))
                            .stream()
                            .map(movieMapper::toMovieSummaryResponse)
                            .toList();
                    return HomeFeedResponse.GenreRowResponse.builder()
                            .genreId(genre.getId())
                            .genreName(genre.getName())
                            .movies(movies)
                            .build();
                })
                .filter(row -> !row.getMovies().isEmpty())
                .toList();

        Long heroMovieId = !recommendedForYou.isEmpty() ? recommendedForYou.get(0).getId()
                : !topRated.isEmpty() ? topRated.get(0).getId()
                : !newest.isEmpty() ? newest.get(0).getId()
                : null;

        MovieDetailResponse heroMovie = heroMovieId != null
                ? movieRepository.findById(heroMovieId).map(this::toDetailWithSimilar).orElse(null)
                : null;

        return HomeFeedResponse.builder()
                .heroMovie(heroMovie)
                .recommendationStatus(recStatus)
                .recommendedForYou(recommendedForYou)
                .topRated(topRated)
                .newest(newest)
                .genreRows(genreRows)
                .build();
    }

    @Transactional(readOnly = true)
    public MovieDetailResponse getMovieDetail(Long id) {
        Movie movie = movieRepository.findById(id)
                .orElseThrow(() -> new AppException(ErrorCode.MOVIE_NOT_FOUND));
        return toDetailWithSimilar(movie);
    }

    private MovieDetailResponse toDetailWithSimilar(Movie movie) {
        MovieDetailResponse detail = movieMapper.toMovieDetailResponse(movie);
        if (movie.getReleaseDate() != null && movie.getOriginalLanguage() != null) {
            LocalDate date = movie.getReleaseDate();
            detail.setSimilarMovies(movieRepository.findRelatedByLanguageAndDate(
                            movie.getId(), movie.getOriginalLanguage(), date.minusYears(5), date.plusYears(5))
                    .stream().map(movieMapper::toMovieSummaryResponse).toList());
        }
        return detail;
    }

    public TrailerResponse getMovieTrailer(Long id) {
        Movie movie = movieRepository.findById(id)
                .orElseThrow(() -> new AppException(ErrorCode.MOVIE_NOT_FOUND));

        if (movie.getTrailerKey() == null || movie.getTrailerKey().isBlank()) {
            throw new AppException(ErrorCode.TRAILER_NOT_FOUND);
        }

        return TrailerResponse.builder()
                .trailerKey(movie.getTrailerKey())
                .embedUrl("https://www.youtube.com/embed/" + movie.getTrailerKey())
                .build();
    }

    @Cacheable("topRatedMovies")
    public List<MovieSummaryResponse> getTopRatedMovies() {
        return movieRepository.findTop50ByImdbRating().stream()
                .map(movieMapper::toMovieSummaryResponse)
                .collect(Collectors.toList());
    }

    @Cacheable("newestMovies")
    public List<MovieSummaryResponse> getNewestMovies() {
        return movieRepository.findTop50ByOrderByReleaseDateDesc().stream()
                .map(movieMapper::toMovieSummaryResponse)
                .collect(Collectors.toList());
    }

    public PageResponse<MovieSummaryResponse> filterMovies(MovieFilterRequest request, Pageable pageable) {
        Specification<Movie> spec = MovieSpecification.filterMovies(request);
        Page<Movie> movies = movieRepository.findAll(spec, pageable);

        List<MovieSummaryResponse> data = movies.getContent().stream()
                .map(movieMapper::toMovieSummaryResponse)
                .toList();

        return PageResponse.<MovieSummaryResponse>builder()
                .currentPage(pageable.getPageNumber() + 1)
                .pageSize(pageable.getPageSize())
                .totalPages(movies.getTotalPages())
                .totalElements(movies.getTotalElements())
                .data(data)
                .build();
    }

    public PageResponse<MovieSummaryResponse> searchMovies(String query, int page, int size) {
        String cleanQuery = query.trim();
        int fetchLimit = 50;
        int queryPage = Math.max(page - 1, 0);

        AiMovieSearchResponse vectorResponse = aiServiceClient.searchSimilarMovies(cleanQuery, fetchLimit);

        if (vectorResponse == null || vectorResponse.getHits() == null) {
            Page<Movie> fallbackPage = movieRepository.searchByTitle(cleanQuery, PageRequest.of(queryPage, size));
            return PageResponse.<MovieSummaryResponse>builder()
                    .currentPage(page)
                    .pageSize(size)
                    .totalPages(fallbackPage.getTotalPages())
                    .totalElements(fallbackPage.getTotalElements())
                    .data(fallbackPage.getContent().stream().map(movieMapper::toMovieSummaryResponse).toList())
                    .build();
        }

        List<Long> rankedIds = vectorResponse.getHits().stream()
                .map(AiMovieSearchResponse.Hit::getMovieId)
                .filter(Objects::nonNull)
                .distinct()
                .toList();

        Map<Long, Movie> movieMap = movieRepository.findAllById(rankedIds).stream()
                .collect(Collectors.toMap(Movie::getId, movie -> movie));

        List<MovieSummaryResponse> hydrated = rankedIds.stream()
                .map(movieMap::get)
                .filter(Objects::nonNull)
                .map(movieMapper::toMovieSummaryResponse)
                .toList();

        int totalElements = hydrated.size();
        int totalPages = (int) Math.ceil((double) totalElements / size);
        long fromIndex = (long) queryPage * size;

        List<MovieSummaryResponse> pagedData = fromIndex >= totalElements ? List.of()
                : hydrated.subList((int) fromIndex, (int) Math.min(fromIndex + size, totalElements));

        return PageResponse.<MovieSummaryResponse>builder()
                .currentPage(page)
                .pageSize(size)
                .totalPages(totalPages)
                .totalElements(totalElements)
                .data(pagedData)
                .build();
    }
}