package com.project.movie_recommendation.service;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.project.movie_recommendation.client.AiServiceClient;
import com.project.movie_recommendation.dto.ai.AiMovieSearchRequest;
import com.project.movie_recommendation.dto.ai.AiMovieSearchResponse;
import com.project.movie_recommendation.dto.response.MovieSummaryResponse;
import com.project.movie_recommendation.entity.Movie;
import com.project.movie_recommendation.mapper.MovieMapper;
import com.project.movie_recommendation.repository.MovieRepository;
import org.junit.jupiter.api.Test;
import org.springframework.data.domain.PageImpl;

import java.util.List;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.*;

class MovieSearchIntegrationTest {
    @Test
    void serializesHybridRerankerContract() throws Exception {
        String body = new ObjectMapper().writeValueAsString(AiMovieSearchRequest.builder()
                .query("space").limit(10).candidateK(50).build());
        assertTrue(body.contains("\"mode\":\"hybrid\""));
        assertTrue(body.contains("\"rerank\":true"));
        assertTrue(body.contains("\"candidate_k\":50"));
    }

    @Test
    void preservesAiRankingAfterHydrationAndDropsMissingIdsBeforePagination() {
        MovieRepository movies = mock(MovieRepository.class);
        MovieMapper mapper = mock(MovieMapper.class);
        AiServiceClient ai = mock(AiServiceClient.class);
        MovieService service = new MovieService(movies, mapper, ai);
        when(ai.searchSimilarMovies("space", 50)).thenReturn(AiMovieSearchResponse.builder()
                .hits(List.of(hit(2L), hit(999L), hit(1L), hit(2L))).build());
        Movie first = Movie.builder().id(1L).title("First").build();
        Movie second = Movie.builder().id(2L).title("Second").build();
        when(movies.findAllById(any())).thenReturn(List.of(first, second));
        when(mapper.toMovieSummaryResponse(any())).thenAnswer(invocation -> {
            Movie movie = invocation.getArgument(0);
            return MovieSummaryResponse.builder().id(movie.getId()).title(movie.getTitle()).build();
        });

        var page = service.searchMovies("space", 0, 10);
        assertEquals(List.of(2L, 1L), page.getData().stream().map(MovieSummaryResponse::getId).toList());
        assertEquals(2, page.getTotalElements());
        verify(movies, never()).searchByTitle(any(), any());
    }

    @Test
    void emptyAiResultsStayEmpty() {
        MovieRepository movies = mock(MovieRepository.class);
        AiServiceClient ai = mock(AiServiceClient.class);
        when(ai.searchSimilarMovies("no match", 50)).thenReturn(
                AiMovieSearchResponse.builder().hits(List.of()).build());

        var page = new MovieService(movies, mock(MovieMapper.class), ai)
                .searchMovies("no match", 0, 10);
        assertEquals(List.of(), page.getData());
        verify(movies, never()).searchByTitle(any(), any());
    }

    @Test
    void unavailableAiFallsBackToLexicalSearch() {
        MovieRepository movies = mock(MovieRepository.class);
        MovieMapper mapper = mock(MovieMapper.class);
        AiServiceClient ai = mock(AiServiceClient.class);
        Movie movie = Movie.builder().id(8L).title("Space Film").build();
        when(ai.searchSimilarMovies("space", 50)).thenReturn(null);
        when(movies.searchByTitle(eq("space"), any())).thenReturn(new PageImpl<>(List.of(movie)));
        when(mapper.toMovieSummaryResponse(movie)).thenReturn(
                MovieSummaryResponse.builder().id(8L).build());

        var page = new MovieService(movies, mapper, ai).searchMovies("space", 0, 10);
        assertEquals(List.of(8L), page.getData().stream().map(MovieSummaryResponse::getId).toList());
        verify(movies).searchByTitle(eq("space"), any());
    }

    private AiMovieSearchResponse.Hit hit(Long id) {
        return AiMovieSearchResponse.Hit.builder().movieId(id).build();
    }
}
