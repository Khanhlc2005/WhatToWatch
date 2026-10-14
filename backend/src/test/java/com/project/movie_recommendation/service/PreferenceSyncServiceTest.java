package com.project.movie_recommendation.service;

import com.project.movie_recommendation.client.AiServiceClient;
import com.project.movie_recommendation.dto.ai.AiRecommendationContracts;
import com.project.movie_recommendation.entity.Movie;
import com.project.movie_recommendation.entity.Rating;
import com.project.movie_recommendation.entity.User;
import com.project.movie_recommendation.repository.RatingRepository;
import com.project.movie_recommendation.repository.UserRepository;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.Test;
import org.springframework.transaction.PlatformTransactionManager;
import org.springframework.transaction.TransactionDefinition;
import org.springframework.transaction.support.SimpleTransactionStatus;
import org.springframework.transaction.support.TransactionSynchronization;
import org.springframework.transaction.support.TransactionSynchronizationManager;

import java.util.List;
import java.util.Optional;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.*;

class PreferenceSyncServiceTest {
    final UserRepository users = mock(UserRepository.class);
    final RatingRepository ratings = mock(RatingRepository.class);
    final AiServiceClient ai = mock(AiServiceClient.class);
    final PlatformTransactionManager transactions = mock(PlatformTransactionManager.class);
    final PreferenceSyncService sync = new PreferenceSyncService(users, ratings, ai, transactions);
    final User user = User.builder().id(1L).build();

    PreferenceSyncServiceTest() {
        when(transactions.getTransaction(any())).thenAnswer(call -> {
            TransactionDefinition definition = call.getArgument(0);
            assertEquals(TransactionDefinition.PROPAGATION_REQUIRES_NEW, definition.getPropagationBehavior());
            assertTrue(definition.isReadOnly());
            return new SimpleTransactionStatus();
        });
        when(users.findById(1L)).thenReturn(Optional.of(user));
        when(ratings.findByUser(user)).thenReturn(List.of());
        when(ai.rebuildPreference(any())).thenReturn(new AiRecommendationContracts.PreferenceResponse("ready"));
    }

    @AfterEach
    void cleanup() {
        TransactionSynchronizationManager.clear();
        sync.stop();
    }

    void begin() {
        TransactionSynchronizationManager.initSynchronization();
        TransactionSynchronizationManager.setActualTransactionActive(true);
    }

    void commit() {
        TransactionSynchronizationManager.getSynchronizations().forEach(TransactionSynchronization::afterCommit);
        TransactionSynchronizationManager.clear();
    }

    @Test
    void sendsOnlyAfterCommitAndCoalescesRepeatedEvents() {
        begin();
        sync.afterCommit(1L);
        sync.afterCommit(1L);
        sync.drain();
        verifyNoInteractions(ai, users, ratings);
        commit();
        sync.drain();
        verify(ai).rebuildPreference(new AiRecommendationContracts.PreferenceSnapshot(1L, List.of()));
        verify(transactions).commit(any());
    }

    @Test
    void rollbackDoesNotQueueSnapshot() {
        begin();
        sync.afterCommit(1L);
        TransactionSynchronizationManager.getSynchronizations().forEach(s ->
                s.afterCompletion(TransactionSynchronization.STATUS_ROLLED_BACK));
        TransactionSynchronizationManager.clear();
        sync.drain();
        verifyNoInteractions(ai, users, ratings);
    }

    @Test
    void refusesCallsWithoutTransaction() {
        assertThrows(IllegalStateException.class, () -> sync.afterCommit(1L));
    }

    @Test
    void nullResponseRetriesLatestSnapshotIncludingLastRatingDeletion() {
        begin();
        sync.afterCommit(1L);
        commit();
        var signal = Rating.builder().user(user).movie(Movie.builder().id(42L).build()).rating(5.0).build();
        when(ratings.findByUser(user)).thenReturn(List.of(signal), List.of());
        when(ai.rebuildPreference(any())).thenReturn(null,
                new AiRecommendationContracts.PreferenceResponse("cold_start"));
        sync.drain();
        sync.drain();
        sync.drain();
        var calls = inOrder(ai);
        calls.verify(ai).rebuildPreference(new AiRecommendationContracts.PreferenceSnapshot(1L,
                List.of(new AiRecommendationContracts.RatingSignal(42L, 5.0))));
        calls.verify(ai).rebuildPreference(new AiRecommendationContracts.PreferenceSnapshot(1L, List.of()));
        calls.verifyNoMoreInteractions();
    }

    @Test
    void commitDuringSendIsNotLost() {
        begin();
        sync.afterCommit(1L);
        commit();
        when(ai.rebuildPreference(any())).thenAnswer(call -> {
            begin();
            sync.afterCommit(1L);
            commit();
            return new AiRecommendationContracts.PreferenceResponse("ready");
        }).thenReturn(new AiRecommendationContracts.PreferenceResponse("ready"));
        sync.drain();
        sync.drain();
        sync.drain();
        verify(ai, times(2)).rebuildPreference(any());
    }

    @Test
    void databaseFailureRemainsQueued() {
        begin();
        sync.afterCommit(1L);
        commit();
        when(ratings.findByUser(user)).thenThrow(new IllegalStateException("unavailable")).thenReturn(List.of());
        sync.drain();
        verifyNoInteractions(ai);
        sync.drain();
        verify(ai).rebuildPreference(any());
    }
}
