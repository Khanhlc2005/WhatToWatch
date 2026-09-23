package com.project.movie_recommendation.controller;

import com.nimbusds.jose.JOSEException;
import com.project.movie_recommendation.dto.request.AuthenticationRequest;
import com.project.movie_recommendation.dto.request.IntrospectRequest;
import com.project.movie_recommendation.dto.response.ApiResponse;
import com.project.movie_recommendation.dto.response.AuthenticationResponse;
import com.project.movie_recommendation.dto.response.IntrospectResponse;
import com.project.movie_recommendation.service.AuthenticationService;
import lombok.AccessLevel;
import lombok.RequiredArgsConstructor;
import lombok.experimental.FieldDefaults;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.text.ParseException;

@RestController
@RequestMapping("/auth")
@RequiredArgsConstructor
@FieldDefaults(level = AccessLevel.PRIVATE, makeFinal = true)
public class AuthenticationController {
    AuthenticationService authenticationService;
    @PostMapping("/log-in")
    ApiResponse<AuthenticationResponse> authenticate(@RequestBody AuthenticationRequest request){
        var resultAuthentication = authenticationService.authenticate(request);
        return ApiResponse.<AuthenticationResponse>builder()
                .result(resultAuthentication)
                .build();
    }

    @PostMapping("/introspect")
    ApiResponse<IntrospectResponse> authenticate(@RequestBody IntrospectRequest request)
            throws ParseException, JOSEException {
        var resultIntrospect = authenticationService.introspect(request);
        return ApiResponse.<IntrospectResponse>builder()
                .result(resultIntrospect)
                .build();
    }

}
