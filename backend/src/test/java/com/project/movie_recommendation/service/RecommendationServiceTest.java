package com.project.movie_recommendation.service;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.project.movie_recommendation.client.AiServiceClient;
import com.project.movie_recommendation.dto.ai.AiRecommendationContracts;
import com.project.movie_recommendation.dto.response.MovieSummaryResponse;
import com.project.movie_recommendation.entity.Movie;
import com.project.movie_recommendation.entity.Rating;
import com.project.movie_recommendation.entity.User;
import com.project.movie_recommendation.mapper.MovieMapper;
import com.project.movie_recommendation.repository.MovieRepository;
import com.project.movie_recommendation.repository.RatingRepository;
import com.project.movie_recommendation.repository.UserRepository;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.Test;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.context.SecurityContextHolder;

import java.util.List;
import java.util.Optional;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.*;

class RecommendationServiceTest {
    @Test
    void parsesFinalRankingResponseSchema() throws Exception {
        String body = """
                {"status":"ready","hits":[{"movie_id":42,"score":0.9,
                "score_components":{"profile_similarity":0.95,"imdb_rating":0.7,
                "weights":{"profile_similarity":0.8,"imdb_rating":0.2}},
                "reasons":[{"code":"profile_similarity","value":0.95}]}]}
                """;
        var response = new ObjectMapper().readValue(
                body, AiRecommendationContracts.RecommendationResponse.class);
        assertEquals(42L, response.hits().get(0).movieId());
        assertEquals(0.95, response.hits().get(0).scoreComponents().profileSimilarity());
        assertEquals("profile_similarity", response.hits().get(0).reasons().get(0).code());
    }

    @Test
    void serializesPreferenceAndRecommendationRequestSchema() throws Exception {
        ObjectMapper mapper = new ObjectMapper();
        String snapshot = mapper.writeValueAsString(new AiRecommendationContracts.PreferenceSnapshot(
                7L, List.of(new AiRecommendationContracts.RatingSignal(42L, 5.0))));
        String request = mapper.writeValueAsString(new AiRecommendationContracts.RecommendationRequest(
                7L, 10, "final", List.of(42L)));
        assertTrue(snapshot.contains("\"user_id\":7"));
        assertTrue(snapshot.contains("\"movie_id\":42"));
        assertTrue(request.contains("\"exclude_movie_ids\":[42]"));
        assertTrue(request.contains("\"ranking\":\"final\""));
    }

    @AfterEach
    void clearSecurityContext() {
        SecurityContextHolder.clearContext();
    }

    @Test
    void coldStartDoesNotWriteAProfile() {
        UserRepository users = mock(UserRepository.class);
        RatingRepository ratings = mock(RatingRepository.class);
        AiServiceClient ai = mock(AiServiceClient.class);
        User user = User.builder().id(7L).email("user@example.com").build();
        SecurityContextHolder.getContext().setAuthentication(
                new UsernamePasswordAuthenticationToken("user@example.com", null));
        when(users.findByEmail("user@example.com")).thenReturn(Optional.of(user));
        when(ratings.findByUser(user)).thenReturn(List.of());
        var service = new RecommendationService(users, ratings, mock(MovieRepository.class),
                mock(MovieMapper.class), ai);

        var result = service.recommend(10);
        assertEquals("cold_start", result.status());
        assertEquals(List.of(), result.hits());
        verifyNoInteractions(ai);
    }

    @Test
    void sendsRealRatingSnapshotAndRequestsFinalRankingWithExclusions() {
        UserRepository users = mock(UserRepository.class);
        RatingRepository ratings = mock(RatingRepository.class);
        MovieRepository movies = mock(MovieRepository.class);
        AiServiceClient ai = mock(AiServiceClient.class);
        User user = User.builder().id(7L).email("user@example.com").build();
        SecurityContextHolder.getContext().setAuthentication(
                new UsernamePasswordAuthenticationToken("user@example.com", null));
        when(users.findByEmail("user@example.com")).thenReturn(Optional.of(user));
        when(ratings.findByUser(user)).thenReturn(List.of(
                rating(user, 1L, 5.0), rating(user, 2L, 4.0), rating(user, 3L, 1.0)));
        when(ai.rebuildPreference(any())).thenAnswer(invocation -> {
            AiRecommendationContracts.PreferenceSnapshot snapshot = invocation.getArgument(0);
            assertEquals(7L, snapshot.userId());
            assertEquals(List.of(1L, 2L, 3L), snapshot.ratings().stream()
                    .map(AiRecommendationContracts.RatingSignal::movieId).toList());
            return new AiRecommendationContracts.PreferenceResponse("ready");
        });
        when(ai.recommendMovies(any())).thenAnswer(invocation -> {
            AiRecommendationContracts.RecommendationRequest request = invocation.getArgument(0);
            assertEquals("final", request.ranking());
            assertEquals(List.of(1L, 2L, 3L), request.excludeMovieIds());
            return new AiRecommendationContracts.RecommendationResponse("ready", List.of(
                    new AiRecommendationContracts.Hit(5L, 0.9, null, List.of()),
                    new AiRecommendationContracts.Hit(4L, 0.8, null, List.of()),
                    new AiRecommendationContracts.Hit(5L, 0.7, null, List.of()),
                    new AiRecommendationContracts.Hit(1L, 0.6, null, List.of())));
        });
        when(movies.findAllById(any())).thenReturn(List.of(
                Movie.builder().id(4L).build(), Movie.builder().id(5L).build()));
        MovieMapper mapper = mock(MovieMapper.class);
        when(mapper.toMovieSummaryResponse(any())).thenAnswer(invocation -> {
            Movie movie = invocation.getArgument(0);
            return MovieSummaryResponse.builder().id(movie.getId()).build();
        });
        var service = new RecommendationService(users, ratings, movies, mapper, ai);

        var result = service.recommend(10);
        assertEquals("ready", result.status());
        assertEquals(List.of(5L, 4L), result.hits().stream()
                .map(hit -> hit.movie().getId()).toList());
        verify(ai).recommendMovies(any());
    }

    private Rating rating(User user, long movieId, double score) {
        return Rating.builder().user(user).movie(Movie.builder().id(movieId).build())
                .rating(score).build();
    }
}
