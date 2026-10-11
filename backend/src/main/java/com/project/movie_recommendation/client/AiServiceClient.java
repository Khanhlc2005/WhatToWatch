package com.project.movie_recommendation.client;

import com.project.movie_recommendation.dto.ai.AiChatRequest;
import com.project.movie_recommendation.dto.ai.AiChatResponse;
import com.project.movie_recommendation.dto.ai.AiMovieSearchRequest;
import com.project.movie_recommendation.dto.ai.AiMovieSearchResponse;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestClient;

@Slf4j
@Component
public class AiServiceClient {

    private final RestClient restClient;

    public AiServiceClient(@Value("${ai-service.url:http://localhost:8010}") String aiServiceUrl) {
        this.restClient = RestClient.builder()
                .baseUrl(aiServiceUrl)
                .build();
    }

    public AiChatResponse sendChatMessage(String message) {
        try {
            return restClient.post()
                    .uri("/internal/chat")
                    .contentType(MediaType.APPLICATION_JSON)
                    .body(AiChatRequest.builder().message(message).build())
                    .retrieve()
                    .body(AiChatResponse.class);
        } catch (Exception e) {
            log.error("Failed to connect to AI Service: {}", e.getMessage());
            return AiChatResponse.builder()
                    .status("error")
                    .reply("Sorry, the AI service is currently unavailable. Please try again later.")
                    .build();
        }
    }

    public AiMovieSearchResponse searchSimilarMovies(String query, int limit) {
        try {
            return restClient.post()
                    .uri("/internal/qdrant/search")
                    .contentType(MediaType.APPLICATION_JSON)
                    .body(AiMovieSearchRequest.builder()
                            .query(query)
                            .mode("dense")
                            .limit(limit)
                            .build())
                    .retrieve()
                    .body(AiMovieSearchResponse.class);
        } catch (Exception e) {
            log.warn("Failed to call Qdrant vector search from AI Service: {}. Falling back to lexical search.", e.getMessage());
            return null;
        }
    }
}