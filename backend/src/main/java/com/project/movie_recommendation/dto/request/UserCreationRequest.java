package com.project.movie_recommendation.dto.request;

import jakarta.validation.constraints.Email;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;
import lombok.*;
import lombok.experimental.FieldDefaults;


@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
@FieldDefaults(level = AccessLevel.PRIVATE)
public class UserCreationRequest {
    @NotBlank(message = "EMAIL_IS_REQUIRED")
    @Email(message = "EMAIL_INVALID")
    String email;

    @Size(min = 8,message = "INVALID_PASSWORD")
    String password;
}

