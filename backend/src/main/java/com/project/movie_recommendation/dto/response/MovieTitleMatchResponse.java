package com.project.movie_recommendation.dto.response;

public record MovieTitleMatchResponse(Long id, String title, String originalTitle, Integer releaseYear) {
}
