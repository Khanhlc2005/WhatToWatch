package com.project.movie_recommendation.entity;

import jakarta.persistence.*;
import lombok.*;
import lombok.experimental.FieldDefaults;
import org.hibernate.annotations.CreationTimestamp;
import org.hibernate.annotations.UpdateTimestamp;

import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Set;

@Entity
@Table(name = "movies", indexes = {
        @Index(name = "idx_movies_release_date", columnList = "release_date"),
        @Index(name = "idx_movies_imdb_rating", columnList = "imdb_rating")
})
@Getter
@Setter
@Builder
@NoArgsConstructor
@AllArgsConstructor
@FieldDefaults(level = AccessLevel.PRIVATE)
public class Movie {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    Long id;

    @Column(name = "imdb_id", length = 30, unique = true)
    String imdbId;

    @Column(name = "tmdb_id", unique = true)
    Long tmdbId;

    @Column(nullable = false, length = 500)
    String title;

    @Column(name = "original_title", length = 500)
    String originalTitle;

    @Column(columnDefinition = "TEXT")
    String overview;

    @Column(length = 500)
    String tagline;

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

    @ManyToMany(fetch = FetchType.LAZY)
    @JoinTable(
            name = "movie_genres",
            joinColumns = @JoinColumn(name = "movie_id"),
            inverseJoinColumns = @JoinColumn(name = "genre_id")
    )
    @Builder.Default
    Set<Genre> genres = new HashSet<>();

    @ManyToMany(fetch = FetchType.LAZY)
    @JoinTable(
            name = "movie_keywords",
            joinColumns = @JoinColumn(name = "movie_id"),
            inverseJoinColumns = @JoinColumn(name = "keyword_id")
    )
    @Builder.Default
    Set<Keyword> keywords = new HashSet<>();

    @OneToMany(mappedBy = "movie", cascade = CascadeType.ALL, orphanRemoval = true)
    @Builder.Default
    List<MovieCast> cast = new ArrayList<>();

    @OneToMany(mappedBy = "movie", cascade = CascadeType.ALL, orphanRemoval = true)
    @Builder.Default
    List<MovieCrew> crew = new ArrayList<>();
}