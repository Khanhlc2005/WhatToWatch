package com.project.movie_recommendation.repository;

import com.project.movie_recommendation.entity.Movie;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.domain.Pageable;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;

@Repository
public interface MovieRepository extends JpaRepository<Movie, String> {
    @Query("select m from Movie m order by case when m.tmdbVoteAverage is not null and m.tmdbVoteAverage > 0 then m.tmdbVoteAverage else coalesce(m.imdbRating, 0) end desc")
    List<Movie> findTopRatedMovies(Pageable pageable);
    List<Movie> findTop10ByOrderByReleaseDateDesc();
    Optional<Movie> findFirstByTitle(String title);
}