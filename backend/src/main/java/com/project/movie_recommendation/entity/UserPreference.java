package com.project.movie_recommendation.entity;

import jakarta.persistence.*;
import lombok.*;
import lombok.experimental.FieldDefaults;

import java.time.LocalDateTime;

@Entity
@Table(name = "user_preferences")
@Getter
@Setter
@Builder
@NoArgsConstructor
@AllArgsConstructor
@FieldDefaults(level = AccessLevel.PRIVATE)
public class UserPreference {

    @Id
    Long userId;

    @OneToOne(fetch = FetchType.LAZY)
    @MapsId
    @JoinColumn(name = "user_id")
    User user;

    @Column(name = "preference_version", length = 50)
    String preferenceVersion;

    @Column(name = "last_rebuilt_at")
    LocalDateTime lastRebuiltAt;

    @Column(name = "profile_stats_json", columnDefinition = "JSON")
    String profileStatsJson;
}