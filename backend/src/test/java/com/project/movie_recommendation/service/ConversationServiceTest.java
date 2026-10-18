package com.project.movie_recommendation.service;

import com.project.movie_recommendation.client.AiServiceClient;
import com.project.movie_recommendation.dto.ai.AiChatHistoryMessage;
import com.project.movie_recommendation.dto.ai.AiChatResponse;
import com.project.movie_recommendation.dto.request.ChatMessageRequest;
import com.project.movie_recommendation.entity.Conversation;
import com.project.movie_recommendation.entity.ConversationMessage;
import com.project.movie_recommendation.entity.User;
import com.project.movie_recommendation.exception.AiServiceUnavailableException;
import com.project.movie_recommendation.repository.ConversationMessageRepository;
import com.project.movie_recommendation.repository.ConversationRepository;
import com.project.movie_recommendation.repository.UserRepository;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.Test;
import org.mockito.ArgumentCaptor;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.context.SecurityContextHolder;

import java.util.ArrayList;
import java.util.List;
import java.util.Optional;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.*;
import static org.mockito.Mockito.*;

class ConversationServiceTest {

    @AfterEach
    void clearSecurityContext() {
        SecurityContextHolder.clearContext();
    }

    @Test
    void sendsSummaryAndTenRecentMessagesWithoutRepeatingCurrentMessage() {
        ConversationRepository conversations = mock(ConversationRepository.class);
        ConversationMessageRepository messages = mock(ConversationMessageRepository.class);
        UserRepository users = mock(UserRepository.class);
        AiServiceClient ai = mock(AiServiceClient.class);
        ConversationService service = new ConversationService(conversations, messages, users, ai);
        User user = User.builder().id(7L).email("user@example.com").build();
        Conversation conversation = Conversation.builder().id(3L).user(user).build();
        SecurityContextHolder.getContext().setAuthentication(
                new UsernamePasswordAuthenticationToken("user@example.com", null));
        when(users.findByEmail("user@example.com")).thenReturn(Optional.of(user));
        when(conversations.findByIdAndUserId(3L, 7L)).thenReturn(Optional.of(conversation));
        List<ConversationMessage> all = new ArrayList<>();
        for (long id = 1; id <= 12; id++) {
            all.add(ConversationMessage.builder().id(id).conversation(conversation)
                    .role(id % 2 == 0 ? "assistant" : "user").content("Tin nhắn " + id).build());
        }
        List<ConversationMessage> descending = new ArrayList<>(all.subList(2, 12));
        java.util.Collections.reverse(descending);
        when(messages.findTop10ByConversationIdOrderByIdDesc(3L)).thenReturn(descending);
        when(messages.findByConversationIdAndIdGreaterThanAndIdLessThanOrderByIdAsc(3L, 0L, 3L))
                .thenReturn(all.subList(0, 2));
        when(ai.sendChatMessage(anyString(), anyList(), anyString())).thenReturn(
                AiChatResponse.builder().status("no_match").reply("Không tìm thấy phim phù hợp.").build());

        service.sendMessage(ChatMessageRequest.builder().conversationId(3L).message("Câu hỏi mới").build());

        @SuppressWarnings("unchecked")
        ArgumentCaptor<List<AiChatHistoryMessage>> history = ArgumentCaptor.forClass(List.class);
        ArgumentCaptor<String> summary = ArgumentCaptor.forClass(String.class);
        verify(ai).sendChatMessage(eq("Câu hỏi mới"), history.capture(), summary.capture());
        assertEquals(10, history.getValue().size());
        assertEquals("Tin nhắn 3", history.getValue().get(0).getContent());
        assertEquals("Tin nhắn 12", history.getValue().get(9).getContent());
        assertTrue(summary.getValue().contains("Tin nhắn 1"));
        assertTrue(summary.getValue().contains("Tin nhắn 2"));
        assertFalse(summary.getValue().contains("Câu hỏi mới"));
        assertEquals(2L, conversation.getSummaryThroughMessageId());
    }

    @Test
    void unavailableAiDoesNotSaveAnAssistantMessage() {
        ConversationRepository conversations = mock(ConversationRepository.class);
        ConversationMessageRepository messages = mock(ConversationMessageRepository.class);
        UserRepository users = mock(UserRepository.class);
        AiServiceClient ai = mock(AiServiceClient.class);
        ConversationService service = new ConversationService(conversations, messages, users, ai);
        User user = User.builder().id(7L).email("user@example.com").build();
        SecurityContextHolder.getContext().setAuthentication(
                new UsernamePasswordAuthenticationToken("user@example.com", null));
        when(users.findByEmail("user@example.com")).thenReturn(Optional.of(user));
        when(conversations.save(any(Conversation.class))).thenAnswer(invocation -> {
            Conversation conversation = invocation.getArgument(0);
            conversation.setId(3L);
            return conversation;
        });
        when(ai.sendChatMessage(anyString(), anyList(), nullable(String.class)))
                .thenReturn(AiChatResponse.builder().status("error").reply("AI unavailable").build());

        assertThrows(AiServiceUnavailableException.class, () -> service.sendMessage(
                ChatMessageRequest.builder().message("Recommend a movie").build()));
        verify(messages, times(1)).save(any(ConversationMessage.class));
    }
}
