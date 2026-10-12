package com.project.movie_recommendation.client;

import com.project.movie_recommendation.dto.ai.AiChatRequest;
import com.project.movie_recommendation.dto.ai.AiChatHistoryMessage;
import com.project.movie_recommendation.dto.ai.AiChatResponse;
import com.project.movie_recommendation.dto.ai.AiMovieSearchRequest;
import com.project.movie_recommendation.dto.ai.AiMovieSearchResponse;
import com.project.movie_recommendation.dto.ai.AiRecommendationContracts;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.MediaType;
import org.springframework.http.client.SimpleClientHttpRequestFactory;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestClient;
import java.util.List;

import java.time.Duration;

@Slf4j
@Component
public class AiServiceClient {

    private final RestClient searchClient;
    private final RestClient chatClient;

    public AiServiceClient(
            @Value("${ai-service.url:http://localhost:8010}") String aiServiceUrl,
            @Value("${ai-service.search-timeout-seconds:35}") int searchTimeoutSeconds,
            @Value("${ai-service.chat-timeout-seconds:390}") int chatTimeoutSeconds) {
        this.searchClient = client(aiServiceUrl, searchTimeoutSeconds);
        this.chatClient = client(aiServiceUrl, chatTimeoutSeconds);
    }

    private static RestClient client(String aiServiceUrl, int readTimeoutSeconds) {
        SimpleClientHttpRequestFactory requestFactory = new SimpleClientHttpRequestFactory();
        requestFactory.setConnectTimeout(Duration.ofSeconds(5));
        requestFactory.setReadTimeout(Duration.ofSeconds(readTimeoutSeconds));
        return RestClient.builder()
                .baseUrl(aiServiceUrl)
                .requestFactory(requestFactory)
                .build();
    }

    public AiChatResponse sendChatMessage(String message, List<AiChatHistoryMessage> history, String summary) {
        try {
            return chatClient.post()
                    .uri("/internal/chat")
                    .contentType(MediaType.APPLICATION_JSON)
                    .body(AiChatRequest.builder().message(message).history(history).summary(summary).build())
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
            return searchClient.post()
                    .uri("/internal/qdrant/search")
                    .contentType(MediaType.APPLICATION_JSON)
                    .body(AiMovieSearchRequest.builder()
                            .query(query)
                            .mode("hybrid")
                            .rerank(true)
                            .candidateK(Math.max(50, limit))
                            .limit(limit)
                            .build())
                    .retrieve()
                    .body(AiMovieSearchResponse.class);
        } catch (Exception e) {
            log.warn("Failed to call Qdrant vector search from AI Service: {}. Falling back to lexical search.", e.getMessage());
            return null;
        }
    }

    public AiRecommendationContracts.PreferenceResponse rebuildPreference(
            AiRecommendationContracts.PreferenceSnapshot snapshot) {
        try {
            return searchClient.put()
                    .uri("/internal/preferences/snapshot")
                    .contentType(MediaType.APPLICATION_JSON)
                    .body(snapshot)
                    .retrieve()
                    .body(AiRecommendationContracts.PreferenceResponse.class);
        } catch (Exception e) {
            log.warn("Failed to rebuild AI preference: {}", e.getMessage());
            return null;
        }
    }

    public AiRecommendationContracts.RecommendationResponse recommendMovies(
            AiRecommendationContracts.RecommendationRequest request) {
        try {
            return searchClient.post()
                    .uri("/internal/recommendations")
                    .contentType(MediaType.APPLICATION_JSON)
                    .body(request)
                    .retrieve()
                    .body(AiRecommendationContracts.RecommendationResponse.class);
        } catch (Exception e) {
            log.warn("Failed to fetch AI recommendations: {}", e.getMessage());
            return null;
        }
    }
}
