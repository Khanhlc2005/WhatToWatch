package com.project.movie_recommendation.entity;

import jakarta.persistence.*;
import lombok.*;
import lombok.experimental.FieldDefaults;

@Entity
@Table(name = "people")
@Getter
@Setter
@Builder
@NoArgsConstructor
@AllArgsConstructor
@FieldDefaults(level = AccessLevel.PRIVATE)
public class Person {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    Long id;

    @Column(name = "tmdb_person_id", unique = true)
    Long tmdbPersonId;

    @Column(name = "imdb_person_id", length = 30, unique = true)
    String imdbPersonId;

    @Column(nullable = false, length = 255)
    String name;
}