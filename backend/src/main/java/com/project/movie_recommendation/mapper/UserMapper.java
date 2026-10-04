package com.project.movie_recommendation.mapper;

import com.project.movie_recommendation.dto.request.UserCreationRequest;
import com.project.movie_recommendation.dto.response.UserResponse;
import com.project.movie_recommendation.entity.User;
import org.mapstruct.Mapper;
import org.mapstruct.Mapping;

@Mapper(componentModel = "spring")
public interface UserMapper {
    @Mapping(target = "passwordHash", ignore = true)
    User toUser(UserCreationRequest request);
    UserResponse toUserResponse(User user);
}