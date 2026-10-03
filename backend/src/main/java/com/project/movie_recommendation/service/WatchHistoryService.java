package com.project.movie_recommendation.service;

import com.project.movie_recommendation.dto.request.WatchHistoryRequest;
import com.project.movie_recommendation.dto.response.WatchHistoryResponse;
import com.project.movie_recommendation.entity.Movie;
import com.project.movie_recommendation.entity.User;
import com.project.movie_recommendation.entity.WatchHistory;
import com.project.movie_recommendation.exception.AppException;
import com.project.movie_recommendation.exception.ErrorCode;
import com.project.movie_recommendation.repository.MovieRepository;
import com.project.movie_recommendation.repository.UserRepository;
import com.project.movie_recommendation.repository.WatchHistoryRepository;
import lombok.AccessLevel;
import lombok.RequiredArgsConstructor;
import lombok.experimental.FieldDefaults;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
@RequiredArgsConstructor
@FieldDefaults(level = AccessLevel.PRIVATE, makeFinal = true)
public class WatchHistoryService {

    WatchHistoryRepository watchHistoryRepository;
    MovieRepository movieRepository;
    UserRepository userRepository;

    private User getCurrentUser() {
        var context = SecurityContextHolder.getContext();
        String email = context.getAuthentication().getName();
        return userRepository.findByEmail(email)
                .orElseThrow(() -> new AppException(ErrorCode.USER_NOT_EXISTED));
    }

    @Transactional
    public WatchHistoryResponse recordWatchHistory(WatchHistoryRequest request) {
        User user = getCurrentUser();
        Movie movie = movieRepository.findById(request.getMovieId())
                .orElseThrow(() -> new AppException(ErrorCode.MOVIE_NOT_FOUND));

        watchHistoryRepository.findByUserAndMovie(user, movie)
                .ifPresent(watchHistoryRepository::delete);

        WatchHistory watchHistory = WatchHistory.builder()
                .user(user)
                .movie(movie)
                .eventType(request.getEventType() != null ? request.getEventType() : "WATCHING")
                .progressSeconds(request.getProgressSeconds() != null ? request.getProgressSeconds() : 0)
                .build();

        watchHistory = watchHistoryRepository.save(watchHistory);
        return toResponse(watchHistory);
    }

    public Page<WatchHistoryResponse> getMyWatchHistory(Pageable pageable) {
        User user = getCurrentUser();
        return watchHistoryRepository.findByUserOrderByCreatedAtDesc(user, pageable)
                .map(this::toResponse);
    }

    @Transactional
    public void deleteWatchHistoryItem(Long id) {
        User user = getCurrentUser();
        WatchHistory history = watchHistoryRepository.findById(id)
                .orElseThrow(() -> new AppException(ErrorCode.WATCH_HISTORY_NOT_FOUND));

        if (!history.getUser().getId().equals(user.getId())) {
            throw new AppException(ErrorCode.UNAUTHORIZED_ACCESS);
        }

        watchHistoryRepository.delete(history);
    }

    @Transactional
    public void clearAllMyWatchHistory() {
        User user = getCurrentUser();
        watchHistoryRepository.deleteByUser(user);
    }

    private WatchHistoryResponse toResponse(WatchHistory entity) {
        return WatchHistoryResponse.builder()
                .id(entity.getId())
                .movieId(entity.getMovie().getId())
                .title(entity.getMovie().getTitle())
                .posterPath(entity.getMovie().getPosterPath())
                .eventType(entity.getEventType())
                .progressSeconds(entity.getProgressSeconds())
                .createdAt(entity.getCreatedAt())
                .build();
    }
}