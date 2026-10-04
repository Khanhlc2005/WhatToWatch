package com.project.movie_recommendation.controller;

import com.project.movie_recommendation.dto.request.RatingRequest;
import com.project.movie_recommendation.dto.response.ApiResponse;
import com.project.movie_recommendation.dto.response.RatingResponse;
import com.project.movie_recommendation.service.RatingService;
import jakarta.validation.Valid;
import lombok.AccessLevel;
import lombok.RequiredArgsConstructor;
import lombok.experimental.FieldDefaults;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Pageable;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/ratings")
@RequiredArgsConstructor
@FieldDefaults(level = AccessLevel.PRIVATE, makeFinal = true)
public class RatingController {

    RatingService ratingService;

    @PostMapping
    public ApiResponse<RatingResponse> rateMovie(@RequestBody @Valid RatingRequest request) {
        return ApiResponse.<RatingResponse>builder()
                .result(ratingService.rateMovie(request))
                .build();
    }

    @GetMapping("/movie/{movieId}")
    public ApiResponse<RatingResponse> getMyRatingForMovie(@PathVariable Long movieId) {
        return ApiResponse.<RatingResponse>builder()
                .result(ratingService.getMyRatingForMovie(movieId))
                .build();
    }

    @GetMapping("/my-ratings")
    public ApiResponse<Page<RatingResponse>> getMyRatings(
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "20") int size) {
        Pageable pageable = PageRequest.of(page, size);
        return ApiResponse.<Page<RatingResponse>>builder()
                .result(ratingService.getMyRatings(pageable))
                .build();
    }

    @DeleteMapping("/movie/{movieId}")
    public ApiResponse<String> deleteRating(@PathVariable Long movieId) {
        ratingService.deleteRating(movieId);
        return ApiResponse.<String>builder()
                .result("Rating removed successfully")
                .build();
    }
}