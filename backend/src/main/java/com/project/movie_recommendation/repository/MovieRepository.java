package com.project.movie_recommendation.repository;

import com.project.movie_recommendation.entity.Genre;
import com.project.movie_recommendation.entity.Movie;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.JpaSpecificationExecutor;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.time.LocalDate;
import java.util.List;

@Repository
public interface MovieRepository extends JpaRepository<Movie, Long>, JpaSpecificationExecutor<Movie> {
    @Query(value = "SELECT * FROM movies WHERE imdb_rating IS NOT NULL AND imdb_vote_count >= 50000 ORDER BY imdb_rating DESC, imdb_vote_count DESC, id ASC LIMIT 50", nativeQuery = true)
    List<Movie> findTop50ByImdbRating();

    List<Movie> findTop50ByOrderByReleaseDateDesc();

    @Query(value = "SELECT * FROM movies WHERE LOWER(title) LIKE LOWER(CONCAT('%', :query, '%')) OR LOWER(original_title) LIKE LOWER(CONCAT('%', :query, '%')) ORDER BY COALESCE(NULLIF(tmdb_vote_average, 0), imdb_rating, 0) DESC, id ASC",
            countQuery = "SELECT COUNT(*) FROM movies WHERE LOWER(title) LIKE LOWER(CONCAT('%', :query, '%')) OR LOWER(original_title) LIKE LOWER(CONCAT('%', :query, '%'))",
            nativeQuery = true)
    Page<Movie> searchByTitle(String query, Pageable pageable);

    @Query(value = "SELECT * FROM movies WHERE id <> :id AND original_language = :language AND release_date BETWEEN :fromDate AND :toDate ORDER BY COALESCE(NULLIF(tmdb_vote_average, 0), imdb_rating, 0) DESC, id ASC LIMIT 6", nativeQuery = true)
    List<Movie> findRelatedByLanguageAndDate(Long id, String language, LocalDate fromDate, LocalDate toDate);

    @Query("SELECT g FROM Movie m JOIN m.genres g GROUP BY g.id, g.name ORDER BY COUNT(m.id) DESC")
    List<Genre> findPopularGenres(Pageable pageable);

    @Query("SELECT m FROM Movie m JOIN m.genres g WHERE g.id = :genreId ORDER BY COALESCE(m.imdbRating, m.tmdbVoteAverage, 0.0) DESC, m.id ASC")
    List<Movie> findTopMoviesByGenreId(@Param("genreId") Long genreId, Pageable pageable);
}