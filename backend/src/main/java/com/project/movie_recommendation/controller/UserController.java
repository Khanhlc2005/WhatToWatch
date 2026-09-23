package com.project.movie_recommendation.controller;

import com.project.movie_recommendation.dto.request.UserCreationRequest;
import com.project.movie_recommendation.dto.response.ApiResponse;
import com.project.movie_recommendation.entity.User;
import com.project.movie_recommendation.service.UserService;
import jakarta.validation.Valid;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/users")
public class UserController {
    @Autowired
    private UserService userService;

    @PostMapping
    ApiResponse<User> createUser(@RequestBody @Valid UserCreationRequest request){
        ApiResponse<User> apiResponse = new ApiResponse<>();
        apiResponse.setResult(userService.createUser(request));

        return apiResponse;
    }
}
