package com.project.movie_recommendation.service;

import com.project.movie_recommendation.client.AiServiceClient;
import com.project.movie_recommendation.dto.ai.AiRecommendationContracts;
import com.project.movie_recommendation.dto.request.RatingRequest;
import com.project.movie_recommendation.dto.response.PageResponse;
import com.project.movie_recommendation.dto.response.RatingResponse;
import com.project.movie_recommendation.entity.Movie;
import com.project.movie_recommendation.entity.Rating;
import com.project.movie_recommendation.entity.User;
import com.project.movie_recommendation.exception.AppException;
import com.project.movie_recommendation.exception.ErrorCode;
import com.project.movie_recommendation.repository.MovieRepository;
import com.project.movie_recommendation.repository.RatingRepository;
import com.project.movie_recommendation.repository.UserRepository;
import org.springframework.data.domain.PageRequest;
import lombok.AccessLevel;
import lombok.RequiredArgsConstructor;
import lombok.experimental.FieldDefaults;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;
import java.util.concurrent.CompletableFuture;

@Slf4j
@Service
@RequiredArgsConstructor
@FieldDefaults(level = AccessLevel.PRIVATE, makeFinal = true)
public class RatingService {

    RatingRepository ratingRepository;
    MovieRepository movieRepository;
    UserRepository userRepository;
    AiServiceClient aiServiceClient;

    private User getCurrentUser() {
        var context = SecurityContextHolder.getContext();
        String email = context.getAuthentication().getName();
        return userRepository.findByEmail(email)
                .orElseThrow(() -> new AppException(ErrorCode.USER_NOT_EXISTED));
    }

    @Transactional
    public RatingResponse rateMovie(RatingRequest request) {
        User user = getCurrentUser();
        Movie movie = movieRepository.findById(request.getMovieId())
                .orElseThrow(() -> new AppException(ErrorCode.MOVIE_NOT_FOUND));

        if (request.getRating() < 1.0 || request.getRating() > 5.0) {
            throw new AppException(ErrorCode.RATING_INVALID);
        }

        Rating rating = ratingRepository.findByUserAndMovie(user, movie)
                .map(existingRating -> {
                    existingRating.setRating(request.getRating());
                    return existingRating;
                })
                .orElseGet(() -> Rating.builder()
                        .user(user)
                        .movie(movie)
                        .rating(request.getRating())
                        .source("APP")
                        .build());

        rating = ratingRepository.save(rating);

        notifyAiPreferenceUpdate(user.getId());

        return toResponse(rating);
    }

    public RatingResponse getMyRatingForMovie(Long movieId) {
        User user = getCurrentUser();
        return ratingRepository.findByUserAndMovieId(user, movieId)
                .map(this::toResponse)
                .orElse(null);
    }

    @Transactional
    public void deleteRating(Long movieId) {
        User user = getCurrentUser();
        Movie movie = movieRepository.findById(movieId)
                .orElseThrow(() -> new AppException(ErrorCode.MOVIE_NOT_FOUND));

        ratingRepository.findByUserAndMovie(user, movie)
                .ifPresentOrElse(ratingRepository::delete, () -> {
                    throw new AppException(ErrorCode.RATING_NOT_FOUND);
                });

        notifyAiPreferenceUpdate(user.getId());
    }

    private void notifyAiPreferenceUpdate(Long userId) {
        CompletableFuture.runAsync(() -> {
            try {
                User user = userRepository.findById(userId).orElse(null);
                if (user == null) return;

                List<Rating> ratings = ratingRepository.findByUser(user);
                List<AiRecommendationContracts.RatingSignal> signals = ratings.stream()
                        .map(r -> new AiRecommendationContracts.RatingSignal(
                                r.getMovie().getId(), r.getRating()))
                        .toList();

                AiRecommendationContracts.PreferenceSnapshot snapshot =
                        new AiRecommendationContracts.PreferenceSnapshot(userId, signals);

                aiServiceClient.rebuildPreference(snapshot);
                log.info("Triggered AI preference update for User ID: {}", userId);
            } catch (Exception e) {
                log.warn("Failed to sync preference to AI: {}", e.getMessage());
            }
        });
    }

    public PageResponse<RatingResponse> getMyRatings(int page, int size) {
        User user = getCurrentUser();
        Pageable pageable = PageRequest.of(page > 0 ? page - 1 : 0, size);

        Page<Rating> ratingPage = ratingRepository.findByUserOrderByCreatedAtDesc(user, pageable);

        List<RatingResponse> data = ratingPage.getContent().stream()
                .map(this::toResponse)
                .toList();

        return PageResponse.<RatingResponse>builder()
                .currentPage(page)
                .pageSize(size)
                .totalPages(ratingPage.getTotalPages())
                .totalElements(ratingPage.getTotalElements())
                .data(data)
                .build();
    }

    private RatingResponse toResponse(Rating entity) {
        return RatingResponse.builder()
                .id(entity.getId())
                .movieId(entity.getMovie().getId())
                .movieTitle(entity.getMovie().getTitle())
                .moviePoster(entity.getMovie().getPosterPath())
                .rating(entity.getRating())
                .source(entity.getSource())
                .createdAt(entity.getCreatedAt())
                .build();
    }
}