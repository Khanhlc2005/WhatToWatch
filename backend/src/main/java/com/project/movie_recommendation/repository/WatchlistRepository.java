package com.project.movie_recommendation.repository;

import com.project.movie_recommendation.entity.Watchlist;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;

@Repository
public interface WatchlistRepository extends JpaRepository<Watchlist, Long> {
    Optional<Watchlist> findByUserId(Long userId);
    Optional<Watchlist> findByUserIdAndName(Long userId, String name);
    List<Watchlist> findAllByUserIdOrderByCreatedAtDesc(Long userId);
    Optional<Watchlist> findByIdAndUserId(Long id, Long userId);
    boolean existsByUserIdAndNameIgnoreCase(Long userId, String name);
}