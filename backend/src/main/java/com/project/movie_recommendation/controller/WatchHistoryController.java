package com.project.movie_recommendation.controller;

import com.project.movie_recommendation.dto.request.WatchHistoryRequest;
import com.project.movie_recommendation.dto.response.ApiResponse;
import com.project.movie_recommendation.dto.response.WatchHistoryResponse;
import com.project.movie_recommendation.service.WatchHistoryService;
import jakarta.validation.Valid;
import lombok.AccessLevel;
import lombok.RequiredArgsConstructor;
import lombok.experimental.FieldDefaults;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Pageable;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/watch-history")
@RequiredArgsConstructor
@FieldDefaults(level = AccessLevel.PRIVATE, makeFinal = true)
public class WatchHistoryController {

    WatchHistoryService watchHistoryService;

    @PostMapping
    public ApiResponse<WatchHistoryResponse> recordHistory(@RequestBody @Valid WatchHistoryRequest request) {
        return ApiResponse.<WatchHistoryResponse>builder()
                .result(watchHistoryService.recordWatchHistory(request))
                .build();
    }

    @GetMapping
    public ApiResponse<Page<WatchHistoryResponse>> getHistory(
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "20") int size) {
        Pageable pageable = PageRequest.of(page, size);
        return ApiResponse.<Page<WatchHistoryResponse>>builder()
                .result(watchHistoryService.getMyWatchHistory(pageable))
                .build();
    }

    @DeleteMapping("/{id}")
    public ApiResponse<String> deleteHistoryItem(@PathVariable Long id) {
        watchHistoryService.deleteWatchHistoryItem(id);
        return ApiResponse.<String>builder()
                .result("Deleted watch history item successfully")
                .build();
    }

    @DeleteMapping
    public ApiResponse<String> clearAllHistory() {
        watchHistoryService.clearAllMyWatchHistory();
        return ApiResponse.<String>builder()
                .result("Cleared all watch history successfully")
                .build();
    }
}