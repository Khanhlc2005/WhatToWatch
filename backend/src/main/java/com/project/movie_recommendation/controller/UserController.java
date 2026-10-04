package com.project.movie_recommendation.controller;

import com.project.movie_recommendation.dto.request.UserCreationRequest;
import com.project.movie_recommendation.dto.response.ApiResponse;
import com.project.movie_recommendation.dto.response.UserResponse;
import com.project.movie_recommendation.entity.User;
import com.project.movie_recommendation.mapper.UserMapper;
import com.project.movie_recommendation.service.UserService;
import jakarta.validation.Valid;
import lombok.AccessLevel;
import lombok.RequiredArgsConstructor;
import lombok.experimental.FieldDefaults;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/users")
@RequiredArgsConstructor
@FieldDefaults(level = AccessLevel.PRIVATE, makeFinal = true)
public class UserController {
    UserService userService;
    UserMapper userMapper;

    @PostMapping
    public ApiResponse<UserResponse> createUser(@RequestBody @Valid UserCreationRequest request) {
        User user = userService.createUser(request);
        return ApiResponse.<UserResponse>builder()
                .result(userMapper.toUserResponse(user))
                .build();
    }
}