package com.project.movie_recommendation.mapper;

import com.project.movie_recommendation.dto.request.UserCreationRequest;

import com.project.movie_recommendation.entity.User;
import org.mapstruct.Mapper;

@Mapper(componentModel = "spring")
public interface UserMapper {
    User toUser(UserCreationRequest request);
}
