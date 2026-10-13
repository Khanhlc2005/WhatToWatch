package com.project.movie_recommendation.service;

import com.project.movie_recommendation.client.AiServiceClient;
import com.project.movie_recommendation.dto.ai.AiMovieSearchResponse;
import com.project.movie_recommendation.dto.request.MovieFilterRequest;
import com.project.movie_recommendation.dto.response.MovieDetailResponse;
import com.project.movie_recommendation.dto.response.MovieSummaryResponse;
import com.project.movie_recommendation.dto.response.PageResponse;
import com.project.movie_recommendation.dto.response.TrailerResponse;
import com.project.movie_recommendation.entity.Movie;
import com.project.movie_recommendation.exception.AppException;
import com.project.movie_recommendation.exception.ErrorCode;
import com.project.movie_recommendation.mapper.MovieMapper;
import com.project.movie_recommendation.repository.MovieRepository;
import com.project.movie_recommendation.repository.specification.MovieSpecification;
import org.springframework.cache.annotation.Cacheable;
import lombok.AccessLevel;
import lombok.RequiredArgsConstructor;
import lombok.experimental.FieldDefaults;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.domain.Specification;
import org.springframework.stereotype.Service;

import java.util.List;
import java.time.LocalDate;
import java.util.Map;
import java.util.Objects;
import java.util.stream.Collectors;
import org.springframework.data.domain.PageRequest;
import org.springframework.transaction.annotation.Transactional;

@Service
@RequiredArgsConstructor
@FieldDefaults(level = AccessLevel.PRIVATE, makeFinal = true)
public class MovieService {
    MovieRepository movieRepository;
    MovieMapper movieMapper;
    AiServiceClient aiServiceClient;

    @Transactional(readOnly = true)
    public MovieDetailResponse getMovieDetail(Long id) {
        Movie movie = movieRepository.findById(id)
                .orElseThrow(() -> new AppException(ErrorCode.MOVIE_NOT_FOUND));
        MovieDetailResponse detail = movieMapper.toMovieDetailResponse(movie);
        if (movie.getReleaseDate() != null && movie.getOriginalLanguage() != null) {
            LocalDate date = movie.getReleaseDate();
            detail.setSimilarMovies(movieRepository.findRelatedByLanguageAndDate(
                    id, movie.getOriginalLanguage(), date.minusYears(5), date.plusYears(5))
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
