package com.project.movie_recommendation.repository;

import com.project.movie_recommendation.entity.Movie;
import com.project.movie_recommendation.entity.User;
import com.project.movie_recommendation.entity.WatchHistory;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.Optional;

@Repository
public interface WatchHistoryRepository extends JpaRepository<WatchHistory, Long> {
    Page<WatchHistory> findByUserOrderByCreatedAtDesc(User user, Pageable pageable);

    Optional<WatchHistory> findByUserAndMovie(User user, Movie movie);

    void deleteByUser(User user);
}