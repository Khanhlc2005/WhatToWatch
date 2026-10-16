package com.project.movie_recommendation.controller;

import com.project.movie_recommendation.dto.request.WatchlistRequest;
import com.project.movie_recommendation.dto.response.ApiResponse;
import com.project.movie_recommendation.dto.response.PageResponse;
import com.project.movie_recommendation.dto.response.WatchlistItemResponse;
import com.project.movie_recommendation.dto.response.WatchlistResponse;
import com.project.movie_recommendation.dto.response.WatchlistStatusResponse;
import com.project.movie_recommendation.service.WatchlistService;
import jakarta.validation.Valid;
import lombok.AccessLevel;
import lombok.RequiredArgsConstructor;
import lombok.experimental.FieldDefaults;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/watchlists")
@RequiredArgsConstructor
@FieldDefaults(level = AccessLevel.PRIVATE, makeFinal = true)
public class WatchlistController {

    WatchlistService watchlistService;

    @PostMapping
    public ApiResponse<WatchlistResponse> createWatchlist(@RequestBody @Valid WatchlistRequest request) {
        return ApiResponse.<WatchlistResponse>builder()
                .result(watchlistService.createWatchlist(request))
                .build();
    }

    @GetMapping("/lists")
    public ApiResponse<List<WatchlistResponse>> getMyWatchlists() {
        return ApiResponse.<List<WatchlistResponse>>builder()
                .result(watchlistService.getMyWatchlists())
                .build();
    }

    @PutMapping("/{watchlistId}")
    public ApiResponse<WatchlistResponse> updateWatchlist(
            @PathVariable Long watchlistId,
            @RequestBody @Valid WatchlistRequest request) {
        return ApiResponse.<WatchlistResponse>builder()
                .result(watchlistService.updateWatchlist(watchlistId, request))
                .build();
    }

    @DeleteMapping("/{watchlistId}")
    public ApiResponse<String> deleteWatchlist(@PathVariable Long watchlistId) {
        watchlistService.deleteWatchlist(watchlistId);
        return ApiResponse.<String>builder()
                .result("Watchlist deleted successfully")
                .build();
    }

    @PostMapping("/{watchlistId}/movies/{movieId}")
    public ApiResponse<String> addMovieToSpecificWatchlist(
            @PathVariable Long watchlistId,
            @PathVariable Long movieId) {
        watchlistService.addMovieToWatchlist(watchlistId, movieId);
        return ApiResponse.<String>builder()
                .result("Movie added to watchlist successfully")
                .build();
    }

    @DeleteMapping("/{watchlistId}/movies/{movieId}")
    public ApiResponse<String> removeMovieFromSpecificWatchlist(
            @PathVariable Long watchlistId,
            @PathVariable Long movieId) {
        watchlistService.removeMovieFromWatchlist(watchlistId, movieId);
        return ApiResponse.<String>builder()
                .result("Movie removed from watchlist successfully")
                .build();
    }

    @GetMapping("/{watchlistId}/movies")
    public ApiResponse<PageResponse<WatchlistItemResponse>> getWatchlistMovies(
            @PathVariable Long watchlistId,
            @RequestParam(defaultValue = "1") int page,
            @RequestParam(defaultValue = "10") int size) {
        return ApiResponse.<PageResponse<WatchlistItemResponse>>builder()
                .result(watchlistService.getWatchlistItems(watchlistId, page, size))
                .build();
    }

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