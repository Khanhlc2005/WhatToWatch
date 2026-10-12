package com.project.movie_recommendation.dto.ai;

import com.fasterxml.jackson.annotation.JsonProperty;

import java.util.List;
import java.util.Map;

public final class AiRecommendationContracts {
    private AiRecommendationContracts() {}

    public record RatingSignal(@JsonProperty("movie_id") Long movieId, Double rating) {}

    public record PreferenceSnapshot(@JsonProperty("user_id") Long userId, List<RatingSignal> ratings) {}

    public record PreferenceResponse(String status) {}

    public record RecommendationRequest(
            @JsonProperty("user_id") Long userId,
            int limit,
            String ranking,
            @JsonProperty("exclude_movie_ids") List<Long> excludeMovieIds) {}

    public record RecommendationResponse(String status, List<Hit> hits) {}

    public record Hit(
            @JsonProperty("movie_id") Long movieId,
            Double score,
            @JsonProperty("score_components") ScoreComponents scoreComponents,
            List<Reason> reasons) {}

    public record ScoreComponents(
            @JsonProperty("profile_similarity") Double profileSimilarity,
            @JsonProperty("imdb_rating") Double imdbRating,
            Map<String, Double> weights) {}

    public record Reason(String code, Double value) {}
}
