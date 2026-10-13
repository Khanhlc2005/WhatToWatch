package com.project.movie_recommendation.service;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.project.movie_recommendation.client.AiServiceClient;
import com.project.movie_recommendation.dto.ai.AiChatResponse;
import com.project.movie_recommendation.dto.ai.AiChatHistoryMessage;
import com.project.movie_recommendation.dto.request.ChatMessageRequest;
import com.project.movie_recommendation.dto.response.ChatMessageResponse;
import com.project.movie_recommendation.dto.response.ConversationDetailResponse;
import com.project.movie_recommendation.dto.response.ConversationMessageResponse;
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
import java.util.ArrayList;
import java.util.Collections;
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
                    .orElseThrow(() -> new AppException(ErrorCode.UNAUTHORIZED_ACCESS));
        } else {
            String title = request.getMessage().length() > 50
                    ? request.getMessage().substring(0, 47) + "..."
                    : request.getMessage();

            conversation = conversationRepository.save(Conversation.builder()
                    .user(user)
                    .title(title)
                    .build());
        }

        List<ConversationMessage> recent = conversationMessageRepository
                .findTop10ByConversationIdOrderByIdDesc(conversation.getId());
        Collections.reverse(recent);
        updateSummary(conversation, recent);
        List<AiChatHistoryMessage> history = recent.stream().map(message ->
                AiChatHistoryMessage.builder()
                        .role(message.getRole())
                        .content(message.getContent().substring(0, Math.min(2000, message.getContent().length())))
                        .movieIds(movieIds(recommendedMovies(message)))
                        .build()).toList();

        ConversationMessage userMsg = ConversationMessage.builder()
                .conversation(conversation)
                .role("user")
                .content(request.getMessage())
                .build();
        conversationMessageRepository.save(userMsg);

        AiChatResponse aiResult = aiServiceClient.sendChatMessage(
                request.getMessage(), history, conversation.getSummary());

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
                .toolName(aiResult.getToolName())
                .toolPayloadJson(payloadJson)
                .build();
        conversationMessageRepository.save(assistantMsg);
        conversation.setUpdatedAt(LocalDateTime.now());

        return ChatMessageResponse.builder()
                .conversationId(conversation.getId())
                .status(aiResult.getStatus())
                .reply(assistantMsg.getContent())
                .recommendedMovies(aiResult.getMovies() == null ? List.of() : aiResult.getMovies())
                .appliedFilters(aiResult.getAppliedFilters())
                .toolName(aiResult.getToolName())
                .createdAt(assistantMsg.getCreatedAt())
                .build();
    }

    private void updateSummary(Conversation conversation, List<ConversationMessage> recent) {
        if (recent.isEmpty()) return;
        long through = conversation.getSummaryThroughMessageId() == null
                ? 0 : conversation.getSummaryThroughMessageId();
        List<ConversationMessage> older = conversationMessageRepository
                .findByConversationIdAndIdGreaterThanAndIdLessThanOrderByIdAsc(
                        conversation.getId(), through, recent.get(0).getId());
        if (older.isEmpty()) return;
        StringBuilder summary = new StringBuilder(conversation.getSummary() == null ? "" : conversation.getSummary());
        for (ConversationMessage message : older) {
            String content = message.getContent().replaceAll("\\s+", " ").trim();
            if (content.isEmpty()) continue;
            if (!summary.isEmpty()) summary.append("\n");
            summary.append(message.getRole().equals("user") ? "Người dùng: " : "Trợ lý: ")
                    .append(content, 0, Math.min(content.length(), 180));
        }
        String bounded = summary.toString();
        if (bounded.length() > 1600) bounded = bounded.substring(bounded.length() - 1600);
        conversation.setSummary(bounded);
        conversation.setSummaryThroughMessageId(older.get(older.size() - 1).getId());
    }

    private List<AiChatResponse.AiMovieItem> recommendedMovies(ConversationMessage message) {
        if (message.getToolPayloadJson() == null) return List.of();
        try {
            return objectMapper.readValue(message.getToolPayloadJson(), new TypeReference<List<AiChatResponse.AiMovieItem>>() {});
        } catch (JsonProcessingException e) {
            log.warn("Failed to parse recommended movies for message {}", message.getId());
            return List.of();
        }
    }

    private List<Long> movieIds(List<AiChatResponse.AiMovieItem> movies) {
        if (movies == null || movies.isEmpty()) return List.of();

        List<Long> ids = new ArrayList<>();
        for (AiChatResponse.AiMovieItem movie : movies) {
            try {
                long id = Long.parseLong(movie.getMovieId());
                if (id > 0) ids.add(id);
            } catch (NumberFormatException | NullPointerException e) {
                log.warn("Không thể parse ID phim từ AI trả về: {}", movie.getMovieId());
            }
        }
        return ids;
    }

    @Transactional(readOnly = true)
    public ConversationDetailResponse getConversation(Long id) {
        User user = getCurrentUser();
        Conversation conversation = conversationRepository.findByIdAndUserId(id, user.getId())
                .orElseThrow(() -> new AppException(ErrorCode.UNAUTHORIZED_ACCESS));
        List<ConversationMessageResponse> messages = conversationMessageRepository
                .findByConversationIdOrderByIdAsc(id).stream().map(message ->
                        ConversationMessageResponse.builder()
                                .id(message.getId())
                                .role(message.getRole())
                                .content(message.getContent())
                                .recommendedMovies(recommendedMovies(message))
                                .toolName(message.getToolName())
                                .createdAt(message.getCreatedAt())
                                .build()).toList();
        return ConversationDetailResponse.builder()
                .id(conversation.getId()).title(conversation.getTitle()).messages(messages).build();
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
