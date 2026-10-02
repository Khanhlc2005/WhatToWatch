package com.project.movie_recommendation.service;

import com.project.movie_recommendation.dto.response.MovieDetailResponse;
import com.project.movie_recommendation.dto.response.MovieSummaryResponse;
import com.project.movie_recommendation.dto.response.TrailerResponse;
import com.project.movie_recommendation.entity.Movie;
import com.project.movie_recommendation.exception.AppException;
import com.project.movie_recommendation.exception.ErrorCode;
import com.project.movie_recommendation.mapper.MovieMapper;
import com.project.movie_recommendation.repository.MovieRepository;
import lombok.AccessLevel;
import lombok.RequiredArgsConstructor;
import lombok.experimental.FieldDefaults;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.stream.Collectors;

@Service
@RequiredArgsConstructor
@FieldDefaults(level = AccessLevel.PRIVATE, makeFinal = true)
public class MovieService {
    MovieRepository movieRepository;
    MovieMapper movieMapper;

    public MovieDetailResponse getMovieDetail(Long id) {
        Movie movie = movieRepository.findById(id)
                .orElseThrow(() -> new AppException(ErrorCode.MOVIE_NOT_FOUND));
        return movieMapper.toMovieDetailResponse(movie);
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
        return movieRepository.findTop10ByOrderByTmdbVoteAverageDesc().stream()
                .map(movieMapper::toMovieSummaryResponse)
                .collect(Collectors.toList());
    }

    public List<MovieSummaryResponse> getNewestMovies() {
        return movieRepository.findTop10ByOrderByReleaseDateDesc().stream()
                .map(movieMapper::toMovieSummaryResponse)
                .collect(Collectors.toList());
    }
}