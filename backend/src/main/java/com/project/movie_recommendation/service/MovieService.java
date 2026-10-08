package com.project.movie_recommendation.service;

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

import java.util.List;
import java.time.LocalDate;
import org.springframework.data.domain.PageRequest;
import org.springframework.transaction.annotation.Transactional;
import java.util.stream.Collectors;

@Service
@RequiredArgsConstructor
@FieldDefaults(level = AccessLevel.PRIVATE, makeFinal = true)
public class MovieService {
    MovieRepository movieRepository;
    MovieMapper movieMapper;

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
        Page<Movie> movies = movieRepository.searchByTitle(query.trim(), PageRequest.of(page, size));
        return PageResponse.<MovieSummaryResponse>builder()
                .currentPage(page + 1)
                .pageSize(size)
                .totalPages(movies.getTotalPages())
                .totalElements(movies.getTotalElements())
                .data(movies.getContent().stream().map(movieMapper::toMovieSummaryResponse).toList())
                .build();
    }

}
