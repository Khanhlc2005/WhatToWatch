package com.project.movie_recommendation.controller;

import com.project.movie_recommendation.dto.response.ApiResponse;
import com.project.movie_recommendation.dto.response.PageResponse;
import com.project.movie_recommendation.dto.response.WatchlistItemResponse;
import com.project.movie_recommendation.dto.response.WatchlistStatusResponse;
import com.project.movie_recommendation.service.WatchlistService;
import lombok.AccessLevel;
import lombok.RequiredArgsConstructor;
import lombok.experimental.FieldDefaults;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/watchlists")
@RequiredArgsConstructor
@FieldDefaults(level = AccessLevel.PRIVATE, makeFinal = true)
public class WatchlistController {

    WatchlistService watchlistService;

    @PostMapping("/movies/{movieId}")
    public ApiResponse<String> addToWatchlist(@PathVariable Long movieId) {
        watchlistService.addToWatchlist(movieId);
        return ApiResponse.<String>builder()
                .result("Movie added to watchlist successfully")
                .build();
    }

    @DeleteMapping("/movies/{movieId}")
    public ApiResponse<String> removeFromWatchlist(@PathVariable Long movieId) {
        watchlistService.removeFromWatchlist(movieId);
        return ApiResponse.<String>builder()
                .result("Movie removed from watchlist successfully")
                .build();
    }

    @GetMapping("/status")
    public ApiResponse<WatchlistStatusResponse> checkStatus(@RequestParam Long movieId) {
        return ApiResponse.<WatchlistStatusResponse>builder()
                .result(watchlistService.checkStatus(movieId))
                .build();
    }

    @GetMapping
    public ApiResponse<PageResponse<WatchlistItemResponse>> getMyWatchlist(
            @RequestParam(defaultValue = "1") int page,
            @RequestParam(defaultValue = "10") int size
    ) {
        return ApiResponse.<PageResponse<WatchlistItemResponse>>builder()
                .result(watchlistService.getMyWatchlist(page, size))
                .build();
    }
}