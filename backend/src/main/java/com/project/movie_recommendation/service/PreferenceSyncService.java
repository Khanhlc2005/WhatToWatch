package com.project.movie_recommendation.service;

import com.project.movie_recommendation.client.AiServiceClient;
import com.project.movie_recommendation.dto.ai.AiRecommendationContracts;
import com.project.movie_recommendation.repository.RatingRepository;
import com.project.movie_recommendation.repository.UserRepository;
import jakarta.annotation.PostConstruct;
import jakarta.annotation.PreDestroy;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.PlatformTransactionManager;
import org.springframework.transaction.TransactionDefinition;
import org.springframework.transaction.support.TransactionSynchronization;
import org.springframework.transaction.support.TransactionSynchronizationManager;
import org.springframework.transaction.support.TransactionTemplate;

import java.util.Set;
import java.util.HashSet;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.Executors;
import java.util.concurrent.ScheduledExecutorService;
import java.util.concurrent.TimeUnit;

/** Single-process, eventually consistent sync. Pending work is not durable across restarts. */
@Slf4j
@Service
public class PreferenceSyncService {
    private final UserRepository users;
    private final RatingRepository ratings;
    private final AiServiceClient ai;
    private final TransactionTemplate readTransaction;
    private final Set<Long> pending = ConcurrentHashMap.newKeySet();
    private final ScheduledExecutorService worker = Executors.newSingleThreadScheduledExecutor(task -> {
        Thread thread = new Thread(task, "preference-sync");
        thread.setDaemon(true);
        return thread;
    });

    public PreferenceSyncService(UserRepository users, RatingRepository ratings,
                                 AiServiceClient ai, PlatformTransactionManager transactions) {
        this.users = users;
        this.ratings = ratings;
        this.ai = ai;
        this.readTransaction = new TransactionTemplate(transactions);
        readTransaction.setPropagationBehavior(TransactionDefinition.PROPAGATION_REQUIRES_NEW);
        readTransaction.setReadOnly(true);
    }

    @PostConstruct
    void start() {
        worker.scheduleWithFixedDelay(this::drain, 0, 5, TimeUnit.SECONDS);
    }

    public void afterCommit(Long userId) {
        if (!TransactionSynchronizationManager.isActualTransactionActive()
                || !TransactionSynchronizationManager.isSynchronizationActive()) {
            throw new IllegalStateException("Preference sync requires an active rating transaction");
        }
        TransactionSynchronizationManager.registerSynchronization(new TransactionSynchronization() {
            @Override
            public void afterCommit() {
                pending.add(userId);
            }
        });
    }

    // Remove before reading: commits arriving during IO stay queued for the next pass.
    // One worker serializes sends and every retry rereads the complete committed snapshot.
    synchronized void drain() {
        for (Long userId : new HashSet<>(pending)) {
            if (!pending.remove(userId)) continue;
            try {
                var snapshot = readTransaction.execute(status -> users.findById(userId)
                        .map(user -> new AiRecommendationContracts.PreferenceSnapshot(userId,
                                ratings.findByUser(user).stream().map(rating ->
                                        new AiRecommendationContracts.RatingSignal(
                                                rating.getMovie().getId(), rating.getRating())).toList()))
                        .orElse(null));
                if (snapshot == null) continue;
                var response = ai.rebuildPreference(snapshot);
                if (response == null || !("ready".equals(response.status())
                        || "cold_start".equals(response.status()))) {
                    pending.add(userId);
                    log.warn("Preference sync pending retry user_id={}", userId);
                } else {
                    log.info("Preference synced user_id={} status={}", userId, response.status());
                }
            } catch (Exception exception) {
                pending.add(userId);
                log.warn("Preference sync pending retry user_id={} cause={}",
                        userId, exception.getClass().getSimpleName());
            }
        }
    }

    @PreDestroy
    void stop() {
        worker.shutdownNow();
    }
}
