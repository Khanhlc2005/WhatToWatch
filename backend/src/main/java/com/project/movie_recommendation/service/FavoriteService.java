package com.project.movie_recommendation.service;

import com.project.movie_recommendation.dto.response.FavoriteStatusResponse;
import com.project.movie_recommendation.dto.response.MovieSummaryResponse;
import com.project.movie_recommendation.dto.response.PageResponse;
import com.project.movie_recommendation.entity.Favorite;
import com.project.movie_recommendation.entity.Movie;
import com.project.movie_recommendation.entity.User;
import com.project.movie_recommendation.exception.AppException;
import com.project.movie_recommendation.exception.ErrorCode;
import com.project.movie_recommendation.mapper.MovieMapper;
import com.project.movie_recommendation.repository.FavoriteRepository;
import com.project.movie_recommendation.repository.MovieRepository;
import com.project.movie_recommendation.repository.UserRepository;
import lombok.AccessLevel;
import lombok.RequiredArgsConstructor;
import lombok.experimental.FieldDefaults;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Pageable;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;

@Service
@RequiredArgsConstructor
@Slf4j
@FieldDefaults(level = AccessLevel.PRIVATE, makeFinal = true)
public class FavoriteService {

    FavoriteRepository favoriteRepository;
    UserRepository userRepository;
    MovieRepository movieRepository;
    MovieMapper movieMapper;

    private User getAuthenticatedUser() {
        String username = SecurityContextHolder.getContext().getAuthentication().getName();
        return userRepository.findByUsername(username)
                .orElseThrow(() -> new AppException(ErrorCode.USER_NOT_EXISTED));
    }

    @Transactional
    public void addFavorite(Long movieId) {
        User user = getAuthenticatedUser();

        Movie movie = movieRepository.findById(movieId)
                .orElseThrow(() -> new AppException(ErrorCode.MOVIE_NOT_FOUND));

        if (favoriteRepository.existsByUserIdAndMovieId(user.getId(), movieId)) {
            return;
        }

        Favorite favorite = Favorite.builder()
                .user(user)
                .movie(movie)
                .build();

        favoriteRepository.save(favorite);
    }

    @Transactional
    public void removeFavorite(Long movieId) {
        User user = getAuthenticatedUser();
        favoriteRepository.deleteByUserIdAndMovieId(user.getId(), movieId);
    }

    @Transactional(readOnly = true)
    public FavoriteStatusResponse checkFavoriteStatus(Long movieId) {
        User user = getAuthenticatedUser();
        boolean exists = favoriteRepository.existsByUserIdAndMovieId(user.getId(), movieId);

        return FavoriteStatusResponse.builder()
                .movieId(movieId)
                .isFavorite(exists)
                .build();
    }

    @Transactional(readOnly = true)
    public PageResponse<MovieSummaryResponse> getMyFavorites(int page, int size) {
        User user = getAuthenticatedUser();
        Pageable pageable = PageRequest.of(page > 0 ? page - 1 : 0, size);

        Page<Favorite> favoritePage = favoriteRepository.findByUserIdWithMovie(user.getId(), pageable);

        List<MovieSummaryResponse> data = favoritePage.getContent().stream()
                .map(fav -> movieMapper.toMovieSummaryResponse(fav.getMovie()))
                .toList();

        return PageResponse.<MovieSummaryResponse>builder()
                .currentPage(page)
                .pageSize(size)
                .totalPages(favoritePage.getTotalPages())
                .totalElements(favoritePage.getTotalElements())
                .data(data)
                .build();
    }
}