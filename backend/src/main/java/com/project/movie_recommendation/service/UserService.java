package com.project.movie_recommendation.service;

import com.project.movie_recommendation.dto.request.UserCreationRequest;
import com.project.movie_recommendation.entity.User;
import com.project.movie_recommendation.enums.Roles;
import com.project.movie_recommendation.exception.AppException;
import com.project.movie_recommendation.exception.ErrorCode;
import com.project.movie_recommendation.mapper.UserMapper;
import com.project.movie_recommendation.repository.UserRepository;
import lombok.AccessLevel;
import lombok.RequiredArgsConstructor;
import lombok.experimental.FieldDefaults;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;

@Service
@RequiredArgsConstructor
@FieldDefaults(level = AccessLevel.PRIVATE, makeFinal = true)
public class UserService {
    UserRepository userRepository;
    UserMapper userMapper;

    public User createUser(UserCreationRequest request){
        if (userRepository.existsByEmail(request.getEmail()))
            throw new AppException(ErrorCode.USER_EXISTED);

        User user = userMapper.toUser(request);

        if (user.getUsername() == null || user.getUsername().isBlank()) {
            user.setUsername(request.getEmail().split("@")[0]);
        }

        if (userRepository.existsByUsername(user.getUsername())) {
            throw new AppException(ErrorCode.USER_EXISTED);
        }

        user.setRole(Roles.USER);

        PasswordEncoder passwordEncoder = new BCryptPasswordEncoder(10);
        user.setPasswordHash(passwordEncoder.encode(request.getPassword()));

        return userRepository.save(user);
    }
}