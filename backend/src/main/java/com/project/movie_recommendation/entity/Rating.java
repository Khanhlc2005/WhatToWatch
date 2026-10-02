package com.project.movie_recommendation.entity;

import jakarta.persistence.*;
import lombok.*;
import lombok.experimental.FieldDefaults;
import org.hibernate.annotations.CreationTimestamp;

import java.time.LocalDateTime;

@Entity
@Table(name = "ratings",
        uniqueConstraints = {
                @UniqueConstraint(name = "uk_ratings_user_movie", columnNames = {"user_id", "movie_id"})
        },
        indexes = {
                @Index(name = "idx_ratings_user_created_at", columnList = "user_id, created_at")
        }
)
@Getter
@Setter
@Builder
@NoArgsConstructor
@AllArgsConstructor
@FieldDefaults(level = AccessLevel.PRIVATE)
public class Rating {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    Long id;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "user_id", nullable = false)
    User user;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "movie_id", nullable = false)
    Movie movie;

    @Column(nullable = false)
    Double rating;

    @Column(length = 50)
    String source; // "APP" hoặc "MOVIELENS"

    @CreationTimestamp
    @Column(name = "created_at", updatable = false)
    LocalDateTime createdAt;
}