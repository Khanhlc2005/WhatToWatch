package com.project.movie_recommendation.service;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.project.movie_recommendation.client.AiServiceClient;
import com.project.movie_recommendation.dto.ai.AiChatResponse;
import com.project.movie_recommendation.dto.request.ChatMessageRequest;
import com.project.movie_recommendation.dto.response.ChatMessageResponse;
import com.project.movie_recommendation.dto.response.ConversationResponse;
import com.project.movie_recommendation.entity.Conversation;
import com.project.movie_recommendation.entity.ConversationMessage;
import com.project.movie_recommendation.entity.User;
import com.project.movie_recommendation.exception.AppException;
import com.project.movie_recommendation.exception.ErrorCode;
import com.project.movie_recommendation.repository.ConversationMessageRepository;
import com.project.movie_recommendation.repository.ConversationRepository;
import com.project.movie_recommendation.repository.UserRepository;
import lombok.AccessLevel;
import lombok.RequiredArgsConstructor;
import lombok.experimental.FieldDefaults;
import lombok.extern.slf4j.Slf4j;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;
import java.util.List;

@Slf4j
@Service
@RequiredArgsConstructor
@FieldDefaults(level = AccessLevel.PRIVATE, makeFinal = true)
public class ConversationService {

    ConversationRepository conversationRepository;
    ConversationMessageRepository conversationMessageRepository;
    UserRepository userRepository;
    AiServiceClient aiServiceClient;
    ObjectMapper objectMapper = new ObjectMapper();

    private User getCurrentUser() {
        String email = SecurityContextHolder.getContext().getAuthentication().getName();
        return userRepository.findByEmail(email)
                .orElseThrow(() -> new AppException(ErrorCode.USER_NOT_EXISTED));
    }

    @Transactional
    public ChatMessageResponse sendMessage(ChatMessageRequest request) {
        User user = getCurrentUser();

        Conversation conversation;
        if (request.getConversationId() != null) {
            conversation = conversationRepository.findByIdAndUserId(request.getConversationId(), user.getId())
                    .orElseThrow(() -> new AppException(ErrorCode.UNCATEGORIZED_EXCEPTION));
        } else {
            String title = request.getMessage().length() > 50
                    ? request.getMessage().substring(0, 47) + "..."
                    : request.getMessage();

            conversation = conversationRepository.save(Conversation.builder()
                    .user(user)
                    .title(title)
                    .build());
        }

        ConversationMessage userMsg = ConversationMessage.builder()
                .conversation(conversation)
                .role("user")
                .content(request.getMessage())
                .build();
        conversationMessageRepository.save(userMsg);

        AiChatResponse aiResult = aiServiceClient.sendChatMessage(request.getMessage());

        String payloadJson = null;
        if (aiResult.getMovies() != null && !aiResult.getMovies().isEmpty()) {
            try {
                payloadJson = objectMapper.writeValueAsString(aiResult.getMovies());
            } catch (JsonProcessingException e) {
                log.warn("Failed to serialize recommended movies payload: {}", e.getMessage());
            }
        }

        ConversationMessage assistantMsg = ConversationMessage.builder()
                .conversation(conversation)
                .role("assistant")
                .content(aiResult.getReply() != null ? aiResult.getReply() : aiResult.getAnswer())
                .toolPayloadJson(payloadJson)
                .build();
        conversationMessageRepository.save(assistantMsg);

        return ChatMessageResponse.builder()
                .conversationId(conversation.getId())
                .reply(assistantMsg.getContent())
                .recommendedMovies(aiResult.getMovies())
                .createdAt(LocalDateTime.now())
                .build();
    }

    @Transactional(readOnly = true)
    public List<ConversationResponse> getMyConversations() {
        User user = getCurrentUser();
        return conversationRepository.findByUserIdOrderByUpdatedAtDesc(user.getId())
                .stream()
                .map(c -> ConversationResponse.builder()
                        .id(c.getId())
                        .title(c.getTitle())
                        .updatedAt(c.getUpdatedAt())
                        .build())
                .toList();
    }

    @Transactional
    public void deleteConversation(Long conversationId) {
        User user = getCurrentUser();
        Conversation conversation = conversationRepository.findByIdAndUserId(conversationId, user.getId())
                .orElseThrow(() -> new AppException(ErrorCode.UNAUTHORIZED_ACCESS));
        conversationRepository.delete(conversation);
    }
}