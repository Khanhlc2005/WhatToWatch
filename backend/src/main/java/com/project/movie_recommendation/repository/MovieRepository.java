package com.project.movie_recommendation.repository;
import com.project.movie_recommendation.entity.Movie;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.JpaSpecificationExecutor;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.domain.Pageable;
import org.springframework.stereotype.Repository;
import java.util.List;
import java.time.LocalDate;

@Repository
public interface MovieRepository extends JpaRepository<Movie, Long>, JpaSpecificationExecutor<Movie> {
    @Query(value = "SELECT * FROM movies ORDER BY COALESCE(NULLIF(tmdb_vote_average, 0), imdb_rating, 0) DESC, id ASC LIMIT 10", nativeQuery = true)
    List<Movie> findTop10ByEffectiveRating();
    List<Movie> findTop10ByOrderByReleaseDateDesc();

    @Query(value = "SELECT * FROM movies WHERE LOWER(title) LIKE LOWER(CONCAT('%', :query, '%')) OR LOWER(original_title) LIKE LOWER(CONCAT('%', :query, '%')) ORDER BY COALESCE(NULLIF(tmdb_vote_average, 0), imdb_rating, 0) DESC, id ASC",
            countQuery = "SELECT COUNT(*) FROM movies WHERE LOWER(title) LIKE LOWER(CONCAT('%', :query, '%')) OR LOWER(original_title) LIKE LOWER(CONCAT('%', :query, '%'))",
            nativeQuery = true)
    org.springframework.data.domain.Page<Movie> searchByTitle(String query, Pageable pageable);

    @Query(value = "SELECT * FROM movies WHERE id <> :id AND original_language = :language AND release_date BETWEEN :fromDate AND :toDate ORDER BY COALESCE(NULLIF(tmdb_vote_average, 0), imdb_rating, 0) DESC, id ASC LIMIT 6", nativeQuery = true)
    List<Movie> findRelatedByLanguageAndDate(Long id, String language, LocalDate fromDate, LocalDate toDate);
}
