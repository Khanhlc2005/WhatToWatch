package com.project.movie_recommendation.controller;

import com.project.movie_recommendation.dto.response.*;
import com.project.movie_recommendation.service.MovieService;
import com.project.movie_recommendation.dto.request.MovieFilterRequest;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import lombok.AccessLevel;
import lombok.RequiredArgsConstructor;
import lombok.experimental.FieldDefaults;
import org.springframework.web.bind.annotation.*;
import org.springframework.http.HttpStatus;
import org.springframework.web.server.ResponseStatusException;

import java.util.List;

@RestController
@RequestMapping("/movies")
@RequiredArgsConstructor
@FieldDefaults(level = AccessLevel.PRIVATE, makeFinal = true)
public class MovieController {
    MovieService movieService;

    @GetMapping("/{id}")
    public ApiResponse<MovieDetailResponse> getMovieDetail(@PathVariable Long id) {
        return ApiResponse.<MovieDetailResponse>builder()
                .result(movieService.getMovieDetail(id))
                .build();
    }

    @GetMapping("/{id}/trailer")
    public ApiResponse<TrailerResponse> getMovieTrailer(@PathVariable Long id) {
        return ApiResponse.<TrailerResponse>builder()
                .result(movieService.getMovieTrailer(id))
                .build();
    }

    @GetMapping("/home-feed/top-rated")
    public ApiResponse<List<MovieSummaryResponse>> getTopRatedMovies() {
        return ApiResponse.<List<MovieSummaryResponse>>builder()
                .result(movieService.getTopRatedMovies())
                .build();
    }

    @GetMapping("/home-feed/newest")
    public ApiResponse<List<MovieSummaryResponse>> getNewestMovies() {
        return ApiResponse.<List<MovieSummaryResponse>>builder()
                .result(movieService.getNewestMovies())
                .build();
    }

    @GetMapping("/filter")
    public ApiResponse<PageResponse<MovieSummaryResponse>> filterMovies(
            MovieFilterRequest filterRequest,
            Pageable pageable) {
        return ApiResponse.<PageResponse<MovieSummaryResponse>>builder()
                .result(movieService.filterMovies(filterRequest, pageable))
                .build();
    }

    @GetMapping("/search")
    public ApiResponse<PageResponse<MovieSummaryResponse>> searchMovies(
            @RequestParam String query,
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "20") int size) {
        String term = query.trim();
        if (term.isEmpty() || term.length() > 100 || page < 0 || size < 1 || size > 40) {
            throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "Invalid search parameters");
        }
        return ApiResponse.<PageResponse<MovieSummaryResponse>>builder()
                .result(movieService.searchMovies(term, page, size))
                .build();
    }
}
