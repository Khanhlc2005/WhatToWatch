package com.project.movie_recommendation.entity;

import jakarta.persistence.*;
import lombok.*;
import lombok.experimental.FieldDefaults;
import org.hibernate.annotations.CreationTimestamp;

import java.time.LocalDateTime;

@Entity
@Table(name = "conversation_messages", indexes = {
        @Index(name = "idx_messages_conversation_created_at", columnList = "conversation_id, created_at")
})
@Getter
@Setter
@Builder
@NoArgsConstructor
@AllArgsConstructor
@FieldDefaults(level = AccessLevel.PRIVATE)
public class ConversationMessage {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    Long id;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "conversation_id", nullable = false)
    Conversation conversation;

    @Column(nullable = false, length = 50)
    String role;

    @Column(columnDefinition = "TEXT", nullable = false)
    String content;

    @Column(name = "tool_name", length = 100)
    String toolName;

    @Column(name = "tool_payload_json", columnDefinition = "JSON")
    String toolPayloadJson;

    @CreationTimestamp
    @Column(name = "created_at", updatable = false)
    LocalDateTime createdAt;
}