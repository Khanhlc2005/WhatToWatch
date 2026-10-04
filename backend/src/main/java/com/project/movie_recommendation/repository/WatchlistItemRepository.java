package com.project.movie_recommendation.repository;

import com.project.movie_recommendation.entity.WatchlistItem;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.Optional;

@Repository
public interface WatchlistItemRepository extends JpaRepository<WatchlistItem, Long> {
    boolean existsByWatchlistIdAndMovieId(Long watchlistId, Long movieId);

    Optional<WatchlistItem> findByWatchlistIdAndMovieId(Long watchlistId, Long movieId);

    void deleteByWatchlistIdAndMovieId(Long watchlistId, Long movieId);

    Page<WatchlistItem> findByWatchlistIdOrderByCreatedAtDesc(Long watchlistId, Pageable pageable);
}