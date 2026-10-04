package com.project.movie_recommendation.controller;

import com.project.movie_recommendation.dto.response.ApiResponse;
import com.project.movie_recommendation.dto.response.MovieDetailResponse;
import com.project.movie_recommendation.dto.response.MovieSummaryResponse;
import com.project.movie_recommendation.dto.response.TrailerResponse;
import com.project.movie_recommendation.service.MovieService;
import lombok.AccessLevel;
import lombok.RequiredArgsConstructor;
import lombok.experimental.FieldDefaults;
import org.springframework.web.bind.annotation.*;

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
}