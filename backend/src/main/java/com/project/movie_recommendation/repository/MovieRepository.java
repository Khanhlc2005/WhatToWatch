package com.project.movie_recommendation.repository;

import com.project.movie_recommendation.entity.Movie;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;

@Repository
public interface MovieRepository extends JpaRepository<Movie, String> {
    List<Movie> findTop10ByOrderByVoteAverageDesc();
    List<Movie> findTop10ByOrderByReleaseDateDesc();
    Optional<Movie> findFirstByTitle(String title);
}