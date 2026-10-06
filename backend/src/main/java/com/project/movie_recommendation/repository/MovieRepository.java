package com.project.movie_recommendation.repository;

import com.project.movie_recommendation.entity.Movie;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.JpaSpecificationExecutor;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface MovieRepository extends JpaRepository<Movie, Long>, JpaSpecificationExecutor<Movie> {
    List<Movie> findTop10ByOrderByTmdbVoteAverageDesc();
    List<Movie> findTop10ByOrderByReleaseDateDesc();
}