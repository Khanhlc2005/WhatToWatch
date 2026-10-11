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
import lombok.AccessLevel;
import lombok.RequiredArgsConstructor;
import lombok.experimental.FieldDefaults;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.domain.Specification;
import org.springframework.stereotype.Service;

import java.util.Collections;
import java.util.HashMap;
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
    private static final int RRF_K = 60;

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

    public List<MovieSummaryResponse> getTopRatedMovies() {
        return movieRepository.findTop10ByEffectiveRating().stream()
                .map(movieMapper::toMovieSummaryResponse)
                .collect(Collectors.toList());
    }

    public List<MovieSummaryResponse> getNewestMovies() {
        return movieRepository.findTop10ByOrderByReleaseDateDesc().stream()
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

        List<Movie> lexicalMovies = movieRepository.searchByTitle(cleanQuery, PageRequest.of(0, fetchLimit)).getContent();

        AiMovieSearchResponse vectorResponse = aiServiceClient.searchSimilarMovies(cleanQuery, fetchLimit);
        List<Long> semanticMovieIds = Collections.emptyList();
        if (vectorResponse != null && vectorResponse.getHits() != null) {
            semanticMovieIds = vectorResponse.getHits().stream()
                    .map(AiMovieSearchResponse.Hit::getMovieId)
                    .filter(Objects::nonNull)
                    .toList();
        }

        if (semanticMovieIds.isEmpty()) {
            Page<Movie> fallbackPage = movieRepository.searchByTitle(cleanQuery, PageRequest.of(page, size));
            return PageResponse.<MovieSummaryResponse>builder()
                    .currentPage(page + 1)
                    .pageSize(size)
                    .totalPages(fallbackPage.getTotalPages())
                    .totalElements(fallbackPage.getTotalElements())
                    .data(fallbackPage.getContent().stream().map(movieMapper::toMovieSummaryResponse).toList())
                    .build();
        }

        Map<Long, Double> rrfScores = new HashMap<>();

        for (int rank = 0; rank < lexicalMovies.size(); rank++) {
            Long movieId = lexicalMovies.get(rank).getId();
            double score = 1.0 / (RRF_K + (rank + 1));
            rrfScores.merge(movieId, score, Double::sum);
        }

        for (int rank = 0; rank < semanticMovieIds.size(); rank++) {
            Long movieId = semanticMovieIds.get(rank);
            double score = 1.0 / (RRF_K + (rank + 1));
            rrfScores.merge(movieId, score, Double::sum);
        }

        List<Long> sortedIds = rrfScores.entrySet().stream()
                .sorted(Map.Entry.<Long, Double>comparingByValue().reversed())
                .map(Map.Entry::getKey)
                .toList();

        int totalElements = sortedIds.size();
        int totalPages = (int) Math.ceil((double) totalElements / size);
        int fromIndex = page * size;

        List<MovieSummaryResponse> pagedData = Collections.emptyList();
        if (fromIndex < totalElements) {
            int toIndex = Math.min(fromIndex + size, totalElements);
            List<Long> pageIds = sortedIds.subList(fromIndex, toIndex);

            Map<Long, Movie> movieMap = movieRepository.findAllById(pageIds).stream()
                    .collect(Collectors.toMap(Movie::getId, m -> m));

            pagedData = pageIds.stream()
                    .map(movieMap::get)
                    .filter(Objects::nonNull)
                    .map(movieMapper::toMovieSummaryResponse)
                    .toList();
        }

        return PageResponse.<MovieSummaryResponse>builder()
                .currentPage(page + 1)
                .pageSize(size)
                .totalPages(totalPages)
                .totalElements(totalElements)
                .data(pagedData)
                .build();
    }

}
