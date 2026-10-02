package com.project.movie_recommendation.repository;

import com.project.movie_recommendation.entity.Favorite;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Modifying;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.util.Optional;

@Repository
public interface FavoriteRepository extends JpaRepository<Favorite, Long> {

    boolean existsByUserIdAndMovieId(Long userId, Long movieId);

    Optional<Favorite> findByUserIdAndMovieId(Long userId, Long movieId);

    @Modifying
    @Query("DELETE FROM Favorite f WHERE f.user.id = :userId AND f.movie.id = :movieId")
    void deleteByUserIdAndMovieId(@Param("userId") Long userId, @Param("movieId") Long movieId);

    @Query("SELECT f FROM Favorite f JOIN FETCH f.movie WHERE f.user.id = :userId ORDER BY f.createdAt DESC")
    Page<Favorite> findByUserIdWithMovie(@Param("userId") Long userId, Pageable pageable);
}