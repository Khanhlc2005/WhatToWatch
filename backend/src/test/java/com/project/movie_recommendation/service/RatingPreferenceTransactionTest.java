package com.project.movie_recommendation.service;

import com.project.movie_recommendation.client.AiServiceClient;
import com.project.movie_recommendation.dto.ai.AiRecommendationContracts;
import com.project.movie_recommendation.dto.request.RatingRequest;
import com.project.movie_recommendation.entity.Movie;
import com.project.movie_recommendation.entity.Rating;
import com.project.movie_recommendation.entity.User;
import com.project.movie_recommendation.repository.MovieRepository;
import com.project.movie_recommendation.repository.RatingRepository;
import com.project.movie_recommendation.repository.UserRepository;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.Test;
import org.springframework.aop.framework.ProxyFactory;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.transaction.TransactionDefinition;
import org.springframework.transaction.annotation.AnnotationTransactionAttributeSource;
import org.springframework.transaction.interceptor.TransactionInterceptor;
import org.springframework.transaction.support.AbstractPlatformTransactionManager;
import org.springframework.transaction.support.DefaultTransactionStatus;

import java.util.List;
import java.util.Optional;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.*;

/** Real Spring transaction interceptor/synchronization; repositories and AI remain mocks. */
class RatingPreferenceTransactionTest {
    final UserRepository users = mock(UserRepository.class);
    final RatingRepository ratings = mock(RatingRepository.class);
    final MovieRepository movies = mock(MovieRepository.class);
    final AiServiceClient ai = mock(AiServiceClient.class);
    final TestTransactions transactions = new TestTransactions();
    final PreferenceSyncService sync = new PreferenceSyncService(users, ratings, ai, transactions);
    final User user = User.builder().id(1L).email("test@example.com").build();
    final Movie movie = Movie.builder().id(42L).title("Test fixture").build();
    final RatingService service;

    RatingPreferenceTransactionTest() {
        SecurityContextHolder.getContext().setAuthentication(
                new UsernamePasswordAuthenticationToken("test@example.com", null));
        when(users.findByEmail("test@example.com")).thenReturn(Optional.of(user));
        when(users.findById(1L)).thenReturn(Optional.of(user));
        when(movies.findById(42L)).thenReturn(Optional.of(movie));
        when(ratings.findByUserAndMovie(user, movie)).thenReturn(Optional.empty());
        when(ratings.findByUser(user)).thenAnswer(call -> {
            assertTrue(transactions.committed, "Snapshot must be read after rating commit");
            return List.of();
        });
        when(ratings.save(any())).thenAnswer(call -> {
            sync.drain();
            verifyNoInteractions(ai);
            return call.getArgument(0);
        });
        when(ai.rebuildPreference(any())).thenReturn(new AiRecommendationContracts.PreferenceResponse("cold_start"));
        var target = new RatingService(ratings, movies, users, sync);
        ProxyFactory proxy = new ProxyFactory(target);
        proxy.addAdvice(new TransactionInterceptor(transactions, new AnnotationTransactionAttributeSource()));
        service = (RatingService) proxy.getProxy();
    }

    @AfterEach
    void cleanup() {
        SecurityContextHolder.clearContext();
        sync.stop();
    }

    @Test
    void ratingCreationQueuesOnlyAfterActualSpringCommit() {
        doAnswer(call -> {
            assertTrue(transactions.committed);
            return List.of(Rating.builder().user(user).movie(movie).rating(5.0).build());
        }).when(ratings).findByUser(user);
        service.rateMovie(RatingRequest.builder().movieId(42L).rating(5.0).build());
        assertTrue(transactions.committed);
        verifyNoInteractions(ai);
        sync.drain();
        verify(ai).rebuildPreference(new AiRecommendationContracts.PreferenceSnapshot(1L,
                List.of(new AiRecommendationContracts.RatingSignal(42L, 5.0))));
    }

    @Test
    void ratingUpdateReusesExistingRatingAndSendsUpdatedScore() {
        Rating existing = Rating.builder().id(9L).user(user).movie(movie).rating(1.0).build();
        when(ratings.findByUserAndMovie(user, movie)).thenReturn(Optional.of(existing));
        doAnswer(call -> {
            assertTrue(transactions.committed);
            return List.of(existing);
        }).when(ratings).findByUser(user);
        service.rateMovie(RatingRequest.builder().movieId(42L).rating(4.0).build());
        sync.drain();
        verify(ratings).save(existing);
        verify(ai).rebuildPreference(new AiRecommendationContracts.PreferenceSnapshot(1L,
                List.of(new AiRecommendationContracts.RatingSignal(42L, 4.0))));
    }

    @Test
    void deletionOfLastRatingSendsEmptySnapshot() {
        when(ratings.findByUserAndMovie(user, movie)).thenReturn(Optional.of(
                Rating.builder().user(user).movie(movie).rating(5.0).build()));
        service.deleteRating(42L);
        sync.drain();
        verify(ratings).delete(any());
        verify(ai).rebuildPreference(new AiRecommendationContracts.PreferenceSnapshot(1L, List.of()));
    }

    @Test
    void failedCommitNeverSendsPreference() {
        transactions.failCommit = true;
        assertThrows(IllegalStateException.class, () -> service.rateMovie(
                RatingRequest.builder().movieId(42L).rating(5.0).build()));
        sync.drain();
        verifyNoInteractions(ai);
    }

    static class TestTransactions extends AbstractPlatformTransactionManager {
        boolean committed;
        boolean failCommit;
        @Override protected Object doGetTransaction() { return new Object(); }
        @Override protected void doBegin(Object transaction, TransactionDefinition definition) {}
        @Override protected void doCommit(DefaultTransactionStatus status) {
            if (failCommit) throw new IllegalStateException("mock commit failure");
            committed = true;
        }
        @Override protected void doRollback(DefaultTransactionStatus status) {}
    }
}
