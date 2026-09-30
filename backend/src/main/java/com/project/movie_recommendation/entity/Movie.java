package com.project.movie_recommendation.entity;

import jakarta.persistence.*;
import lombok.*;
import lombok.experimental.FieldDefaults;
import org.hibernate.annotations.CreationTimestamp;
import org.hibernate.annotations.UpdateTimestamp;

import java.time.LocalDate;
import java.time.LocalDateTime;

@Entity
@Table(name = "movie")
@Getter
@Setter
@Builder
@NoArgsConstructor
@AllArgsConstructor
@FieldDefaults(level = AccessLevel.PRIVATE)
public class Movie {

    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    String id;

    @Column(name = "imdb_id", length = 30)
    String imdbId;

    @Column(name = "tmdb_id")
    Long tmdbId;

    @Column(nullable = false, length = 500)
    String title;

    @Column(name = "original_title", length = 500)
    String originalTitle;

    @Column(columnDefinition = "TEXT")
    String overview;

    @Column(length = 500)
    String tagline;

    String genres;
    String cast;

    @Column(name = "release_date")
    LocalDate releaseDate;

    @Column(name = "runtime_minutes")
    Integer runtimeMinutes;

    @Column(name = "original_language", length = 10)
    String originalLanguage;

    @Column(name = "adult")
    Boolean adult;

    @Column(name = "imdb_rating")
    Double imdbRating;

    @Column(name = "imdb_vote_count")
    Long imdbVoteCount;

    @Column(name = "tmdb_vote_average")
    Double tmdbVoteAverage;

    @Column(name = "tmdb_popularity")
    Double tmdbPopularity;

    @Column(length = 50)
    String status;

    @Column(name = "poster_path", length = 500)
    String posterPath;

    @Column(name = "backdrop_path", length = 500)
    String backdropPath;

    @Column(name = "trailer_key", length = 100)
    String trailerKey;

    @Column(name = "trailer_site", length = 50)
    String trailerSite;

    @Column(name = "trailer_type", length = 50)
    String trailerType;

    @CreationTimestamp
    @Column(name = "created_at", updatable = false)
    LocalDateTime createdAt;

    @UpdateTimestamp
    @Column(name = "updated_at")
    LocalDateTime updatedAt;
}