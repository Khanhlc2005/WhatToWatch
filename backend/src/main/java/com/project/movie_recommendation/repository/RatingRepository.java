package com.project.movie_recommendation.repository;

import com.project.movie_recommendation.entity.Movie;
import com.project.movie_recommendation.entity.Rating;
import com.project.movie_recommendation.entity.User;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.Optional;

@Repository
public interface RatingRepository extends JpaRepository<Rating, Long> {
    Optional<Rating> findByUserAndMovie(User user, Movie movie);

    Optional<Rating> findByUserAndMovieId(User user, Long movieId);

    Page<Rating> findByUserOrderByCreatedAtDesc(User user, Pageable pageable);

    void deleteByUserAndMovie(User user, Movie movie);
}