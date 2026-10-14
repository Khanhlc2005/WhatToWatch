package com.project.movie_recommendation.client;

import com.project.movie_recommendation.dto.ai.AiRecommendationContracts;
import org.junit.jupiter.api.Test;
import org.springframework.http.HttpMethod;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.test.web.client.MockRestServiceServer;
import org.springframework.web.client.RestClient;

import java.net.SocketTimeoutException;
import java.util.List;

import static org.junit.jupiter.api.Assertions.*;
import static org.springframework.test.web.client.match.MockRestRequestMatchers.*;
import static org.springframework.test.web.client.response.MockRestResponseCreators.*;

class AiServiceClientTest {
    final RestClient.Builder builder = RestClient.builder().baseUrl("http://ai.invalid");
    final MockRestServiceServer server = MockRestServiceServer.bindTo(builder).build();
    final RestClient rest = builder.build();
    final AiServiceClient ai = new AiServiceClient(rest, rest);
    final AiRecommendationContracts.PreferenceSnapshot snapshot =
            new AiRecommendationContracts.PreferenceSnapshot(1L, List.of());
    final AiRecommendationContracts.RecommendationRequest request =
            new AiRecommendationContracts.RecommendationRequest(1L, 10, "final", List.of(42L));

    @Test
    void preferenceUnavailableReturnsNullForWorkerRetry() {
        server.expect(requestTo("http://ai.invalid/internal/preferences/snapshot"))
                .andExpect(method(HttpMethod.PUT)).andExpect(content().json("{\"user_id\":1,\"ratings\":[]}"))
                .andRespond(withStatus(HttpStatus.SERVICE_UNAVAILABLE));
        assertNull(ai.rebuildPreference(snapshot));
        server.verify();
    }

    @Test
    void preferenceTimeoutReturnsNullForWorkerRetry() {
        server.expect(requestTo("http://ai.invalid/internal/preferences/snapshot"))
                .andRespond(req -> { throw new SocketTimeoutException("mock timeout"); });
        assertNull(ai.rebuildPreference(snapshot));
        server.verify();
    }

    @Test
    void parsesActualPreferenceResponseIncludingMetadata() {
        server.expect(requestTo("http://ai.invalid/internal/preferences/snapshot"))
                .andRespond(withSuccess("""
                        {"user_id":1,"status":"cold_start","reason":"insufficient_ratings",
                         "profile_version":"ratings-v1","last_updated":"2026-10-14T00:00:00Z",
                         "rating_count":0,"usable_rating_count":0,"skipped_movies":[]}
                        """, MediaType.APPLICATION_JSON));
        var result = ai.rebuildPreference(snapshot);
        assertNotNull(result);
        assertEquals("cold_start", result.status());
        server.verify();
    }

    @Test
    void recommendationTimeoutAndUnavailableReturnNull() {
        server.expect(requestTo("http://ai.invalid/internal/recommendations"))
                .andRespond(req -> { throw new SocketTimeoutException("mock timeout"); });
        server.expect(requestTo("http://ai.invalid/internal/recommendations"))
                .andRespond(withStatus(HttpStatus.SERVICE_UNAVAILABLE));
        assertNull(ai.recommendMovies(request));
        assertNull(ai.recommendMovies(request));
        server.verify();
    }

    @Test
    void searchTimeoutPreservesLexicalFallbackSignal() {
        server.expect(requestTo("http://ai.invalid/internal/qdrant/search"))
                .andRespond(req -> { throw new SocketTimeoutException("mock timeout"); });
        assertNull(ai.searchSimilarMovies("space exploration", 10));
        server.verify();
    }
}
