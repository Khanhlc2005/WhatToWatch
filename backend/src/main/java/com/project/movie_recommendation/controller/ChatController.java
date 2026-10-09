package com.project.movie_recommendation.controller;

import com.project.movie_recommendation.dto.request.ChatMessageRequest;
import com.project.movie_recommendation.dto.response.ApiResponse;
import com.project.movie_recommendation.dto.response.ChatMessageResponse;
import com.project.movie_recommendation.dto.response.ConversationResponse;
import com.project.movie_recommendation.service.ConversationService;
import jakarta.validation.Valid;
import lombok.AccessLevel;
import lombok.RequiredArgsConstructor;
import lombok.experimental.FieldDefaults;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/chat")
@RequiredArgsConstructor
@FieldDefaults(level = AccessLevel.PRIVATE, makeFinal = true)
public class ChatController {

    ConversationService conversationService;

    @PostMapping
    public ApiResponse<ChatMessageResponse> sendMessage(@RequestBody @Valid ChatMessageRequest request) {
        return ApiResponse.<ChatMessageResponse>builder()
                .result(conversationService.sendMessage(request))
                .build();
    }

    @GetMapping("/conversations")
    public ApiResponse<List<ConversationResponse>> getMyConversations() {
        return ApiResponse.<List<ConversationResponse>>builder()
                .result(conversationService.getMyConversations())
                .build();
    }

    @DeleteMapping("/conversations/{id}")
    public ApiResponse<String> deleteConversation(@PathVariable Long id) {
        conversationService.deleteConversation(id);
        return ApiResponse.<String>builder()
                .result("Conversation deleted successfully")
                .build();
    }
}