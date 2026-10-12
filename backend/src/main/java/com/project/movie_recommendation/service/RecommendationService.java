package com.project.movie_recommendation.service;

import com.project.movie_recommendation.client.AiServiceClient;
import com.project.movie_recommendation.dto.ai.AiRecommendationContracts;
import com.project.movie_recommendation.dto.response.RecommendationMovieResponse;
import com.project.movie_recommendation.entity.Movie;
import com.project.movie_recommendation.entity.Rating;
import com.project.movie_recommendation.entity.User;
import com.project.movie_recommendation.exception.AppException;
import com.project.movie_recommendation.exception.ErrorCode;
import com.project.movie_recommendation.mapper.MovieMapper;
import com.project.movie_recommendation.repository.MovieRepository;
import com.project.movie_recommendation.repository.RatingRepository;
import com.project.movie_recommendation.repository.UserRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Set;
import java.util.HashSet;
import java.util.function.Function;
import java.util.stream.Collectors;

@Service
@RequiredArgsConstructor
public class RecommendationService {
    private final UserRepository userRepository;
    private final RatingRepository ratingRepository;
    private final MovieRepository movieRepository;
    private final MovieMapper movieMapper;
    private final AiServiceClient aiServiceClient;

    @Transactional(readOnly = true)
    public RecommendationMovieResponse recommend(int limit) {
        String email = SecurityContextHolder.getContext().getAuthentication().getName();
        User user = userRepository.findByEmail(email)
                .orElseThrow(() -> new AppException(ErrorCode.USER_NOT_EXISTED));
        List<Rating> ratings = ratingRepository.findByUser(user);
        if (ratings.size() < 3) {
            return new RecommendationMovieResponse("cold_start", List.of());
        }
        if (ratings.size() > 10000) {
            return new RecommendationMovieResponse("unavailable", List.of());
        }

        List<AiRecommendationContracts.RatingSignal> signals = ratings.stream()
                .map(rating -> new AiRecommendationContracts.RatingSignal(
                        rating.getMovie().getId(), rating.getRating()))
                .toList();
        AiRecommendationContracts.PreferenceResponse preference = aiServiceClient.rebuildPreference(
                new AiRecommendationContracts.PreferenceSnapshot(user.getId(), signals));
        if (preference == null) {
            return new RecommendationMovieResponse("unavailable", List.of());
        }
        if (!"ready".equals(preference.status())) {
            return new RecommendationMovieResponse(preference.status(), List.of());
        }

        List<Long> excluded = signals.stream()
                .map(AiRecommendationContracts.RatingSignal::movieId)
                .distinct().toList();
        AiRecommendationContracts.RecommendationResponse response = aiServiceClient.recommendMovies(
                new AiRecommendationContracts.RecommendationRequest(user.getId(), limit, "final", excluded));
        if (response == null || response.hits() == null) {
            return new RecommendationMovieResponse("unavailable", List.of());
        }

        Set<Long> excludedSet = Set.copyOf(excluded);
        List<Long> rankedIds = response.hits().stream()
                .map(AiRecommendationContracts.Hit::movieId)
                .filter(Objects::nonNull)
                .filter(id -> !excludedSet.contains(id))
                .distinct().toList();
        Map<Long, Movie> movies = movieRepository.findAllById(rankedIds).stream()
                .collect(Collectors.toMap(Movie::getId, Function.identity()));
        Set<Long> seen = new HashSet<>();
        List<RecommendationMovieResponse.Hit> hits = response.hits().stream()
                .filter(hit -> hit.movieId() != null && !excludedSet.contains(hit.movieId()))
                .filter(hit -> movies.containsKey(hit.movieId()))
                .filter(hit -> seen.add(hit.movieId()))
                .map(hit -> new RecommendationMovieResponse.Hit(
                        movieMapper.toMovieSummaryResponse(movies.get(hit.movieId())),
                        hit.score(), hit.scoreComponents(), hit.reasons()))
                .toList();
        return new RecommendationMovieResponse(response.status(), hits);
    }
}
