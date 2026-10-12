package com.project.movie_recommendation.dto.response;

import com.project.movie_recommendation.dto.ai.AiRecommendationContracts.Reason;
import com.project.movie_recommendation.dto.ai.AiRecommendationContracts.ScoreComponents;

import java.util.List;

public record RecommendationMovieResponse(
        String status,
        List<Hit> hits) {

    public record Hit(MovieSummaryResponse movie, Double score,
                      ScoreComponents scoreComponents, List<Reason> reasons) {}
}
