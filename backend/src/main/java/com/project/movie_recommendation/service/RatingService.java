package com.project.movie_recommendation.service;

import com.project.movie_recommendation.dto.request.RatingRequest;
import com.project.movie_recommendation.dto.response.RatingResponse;
import com.project.movie_recommendation.entity.Movie;
import com.project.movie_recommendation.entity.Rating;
import com.project.movie_recommendation.entity.User;
import com.project.movie_recommendation.exception.AppException;
import com.project.movie_recommendation.exception.ErrorCode;
import com.project.movie_recommendation.repository.MovieRepository;
import com.project.movie_recommendation.repository.RatingRepository;
import com.project.movie_recommendation.repository.UserRepository;
import lombok.AccessLevel;
import lombok.RequiredArgsConstructor;
import lombok.experimental.FieldDefaults;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Slf4j
@Service
@RequiredArgsConstructor
@FieldDefaults(level = AccessLevel.PRIVATE, makeFinal = true)
public class RatingService {

    RatingRepository ratingRepository;
    MovieRepository movieRepository;
    UserRepository userRepository;

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

        notifyAiPreferenceUpdate(user.getId(), movie.getId(), rating.getRating());

        return toResponse(rating);
    }

    public RatingResponse getMyRatingForMovie(Long movieId) {
        User user = getCurrentUser();
        return ratingRepository.findByUserAndMovieId(user, movieId)
                .map(this::toResponse)
                .orElse(null);
    }

    public Page<RatingResponse> getMyRatings(Pageable pageable) {
        User user = getCurrentUser();
        return ratingRepository.findByUserOrderByCreatedAtDesc(user, pageable)
                .map(this::toResponse);
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

        notifyAiPreferenceUpdate(user.getId(), movie.getId(), null);
    }

    private void notifyAiPreferenceUpdate(Long userId, Long movieId, Double ratingScore) {
        log.info("Triggered AI Preference Update Webhook for userId={}, movieId={}, score={}",
                userId, movieId, ratingScore);
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