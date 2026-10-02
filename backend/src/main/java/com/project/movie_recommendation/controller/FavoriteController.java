package com.project.movie_recommendation.controller;

import com.project.movie_recommendation.dto.response.ApiResponse;
import com.project.movie_recommendation.dto.response.FavoriteStatusResponse;
import com.project.movie_recommendation.dto.response.MovieSummaryResponse;
import com.project.movie_recommendation.dto.response.PageResponse;
import com.project.movie_recommendation.service.FavoriteService;
import lombok.AccessLevel;
import lombok.RequiredArgsConstructor;
import lombok.experimental.FieldDefaults;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/favorites")
@RequiredArgsConstructor
@FieldDefaults(level = AccessLevel.PRIVATE, makeFinal = true)
public class FavoriteController {

    FavoriteService favoriteService;

    @PostMapping("/{movieId}")
    public ApiResponse<String> addFavorite(@PathVariable Long movieId) {
        favoriteService.addFavorite(movieId);
        return ApiResponse.<String>builder()
                .result("Added movie to favorites successfully")
                .build();
    }

    @DeleteMapping("/{movieId}")
    public ApiResponse<String> removeFavorite(@PathVariable Long movieId) {
        favoriteService.removeFavorite(movieId);
        return ApiResponse.<String>builder()
                .result("Removed movie from favorites successfully")
                .build();
    }

    @GetMapping("/status")
    public ApiResponse<FavoriteStatusResponse> checkStatus(@RequestParam Long movieId) {
        return ApiResponse.<FavoriteStatusResponse>builder()
                .result(favoriteService.checkFavoriteStatus(movieId))
                .build();
    }

    @GetMapping
    public ApiResponse<PageResponse<MovieSummaryResponse>> getMyFavorites(
            @RequestParam(defaultValue = "1") int page,
            @RequestParam(defaultValue = "10") int size
    ) {
        return ApiResponse.<PageResponse<MovieSummaryResponse>>builder()
                .result(favoriteService.getMyFavorites(page, size))
                .build();
    }
}