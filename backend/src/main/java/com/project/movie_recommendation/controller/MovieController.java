package com.project.movie_recommendation.controller;

import com.project.movie_recommendation.dto.request.MovieFilterRequest;
import com.project.movie_recommendation.dto.response.*;
import com.project.movie_recommendation.exception.AppException;
import com.project.movie_recommendation.exception.ErrorCode;
import com.project.movie_recommendation.service.MovieService;
import com.project.movie_recommendation.service.RecommendationService;
import lombok.AccessLevel;
import lombok.RequiredArgsConstructor;
import lombok.experimental.FieldDefaults;
import org.springframework.data.domain.Pageable;
import org.springframework.security.authentication.AnonymousAuthenticationToken;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/movies")
@RequiredArgsConstructor
@FieldDefaults(level = AccessLevel.PRIVATE, makeFinal = true)
public class MovieController {
    MovieService movieService;
    RecommendationService recommendationService;

    @GetMapping("/home-feed")
    public ApiResponse<HomeFeedResponse> getHomeFeed(
            @RequestParam(defaultValue = "10") int limit) {
        if (limit < 1 || limit > 50) {
            throw new AppException(ErrorCode.INVALID_SEARCH_PARAMS);
        }
        RecommendationMovieResponse recommendation = resolveRecommendationsForHomeFeed(limit);
        return ApiResponse.<HomeFeedResponse>builder()
                .result(movieService.getHomeFeed(recommendation, limit))
                .build();
    }

    private RecommendationMovieResponse resolveRecommendationsForHomeFeed(int limit) {
        Authentication auth = SecurityContextHolder.getContext().getAuthentication();
        if (auth == null || !auth.isAuthenticated() || auth instanceof AnonymousAuthenticationToken) {
            return new RecommendationMovieResponse("guest", List.of());
        }
        try {
            return recommendationService.recommend(limit);
        } catch (Exception e) {
            return new RecommendationMovieResponse("unavailable", List.of());
        }
    }

    @GetMapping("/recommendations")
    public ApiResponse<RecommendationMovieResponse> recommendations(
            @RequestParam(defaultValue = "10") int limit) {
        if (limit < 1 || limit > 100) {
            throw new AppException(ErrorCode.INVALID_SEARCH_PARAMS);
        }
        return ApiResponse.<RecommendationMovieResponse>builder()
                .result(recommendationService.recommend(limit))
                .build();
    }

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
            @RequestParam(defaultValue = "1") int page,
            @RequestParam(defaultValue = "20") int size) {
        String term = query.trim();
        if (term.isEmpty() || term.length() > 100 || page < 0 || size < 1 || size > 40) {
            throw new AppException(ErrorCode.INVALID_SEARCH_PARAMS);
        }
        return ApiResponse.<PageResponse<MovieSummaryResponse>>builder()
                .result(movieService.searchMovies(term, page, size))
                .build();
    }
}