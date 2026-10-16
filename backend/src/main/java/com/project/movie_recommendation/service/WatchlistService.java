package com.project.movie_recommendation.service;

import com.project.movie_recommendation.dto.request.WatchlistRequest;
import com.project.movie_recommendation.dto.response.PageResponse;
import com.project.movie_recommendation.dto.response.WatchlistItemResponse;
import com.project.movie_recommendation.dto.response.WatchlistResponse;
import com.project.movie_recommendation.dto.response.WatchlistStatusResponse;
import com.project.movie_recommendation.entity.Movie;
import com.project.movie_recommendation.entity.User;
import com.project.movie_recommendation.entity.Watchlist;
import com.project.movie_recommendation.entity.WatchlistItem;
import com.project.movie_recommendation.exception.AppException;
import com.project.movie_recommendation.exception.ErrorCode;
import com.project.movie_recommendation.mapper.MovieMapper;
import com.project.movie_recommendation.repository.MovieRepository;
import com.project.movie_recommendation.repository.UserRepository;
import com.project.movie_recommendation.repository.WatchlistItemRepository;
import com.project.movie_recommendation.repository.WatchlistRepository;
import lombok.AccessLevel;
import lombok.RequiredArgsConstructor;
import lombok.experimental.FieldDefaults;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Pageable;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;

@Service
@RequiredArgsConstructor
@FieldDefaults(level = AccessLevel.PRIVATE, makeFinal = true)
public class WatchlistService {

    WatchlistRepository watchlistRepository;
    WatchlistItemRepository watchlistItemRepository;
    MovieRepository movieRepository;
    UserRepository userRepository;
    MovieMapper movieMapper;

    private static final String DEFAULT_WATCHLIST_NAME = "Default Watchlist";

    private User getCurrentUser() {
        var context = SecurityContextHolder.getContext();
        String email = context.getAuthentication().getName();
        return userRepository.findByEmail(email)
                .orElseThrow(() -> new AppException(ErrorCode.USER_NOT_EXISTED));
    }

    private Watchlist getOrCreateDefaultWatchlist(User user) {
        return watchlistRepository.findByUserIdAndName(user.getId(), DEFAULT_WATCHLIST_NAME)
                .or(() -> watchlistRepository.findByUserId(user.getId()))
                .orElseGet(() -> watchlistRepository.save(
                        Watchlist.builder()
                                .user(user)
                                .name(DEFAULT_WATCHLIST_NAME)
                                .build()
                ));
    }

    private Watchlist getOwnedWatchlist(Long watchlistId, Long userId) {
        return watchlistRepository.findByIdAndUserId(watchlistId, userId)
                .orElseThrow(() -> new AppException(ErrorCode.WATCHLIST_NOT_FOUND));
    }

    @Transactional
    public WatchlistResponse createWatchlist(WatchlistRequest request) {
        User user = getCurrentUser();
        String cleanName = request.getName().trim();
        if (cleanName.isEmpty()) {
            throw new AppException(ErrorCode.WATCHLIST_NAME_REQUIRED);
        }
        if (watchlistRepository.existsByUserIdAndNameIgnoreCase(user.getId(), cleanName)) {
            throw new AppException(ErrorCode.WATCHLIST_ALREADY_EXISTS);
        }

        Watchlist watchlist = watchlistRepository.save(
                Watchlist.builder()
                        .user(user)
                        .name(cleanName)
                        .build()
        );

        return toWatchlistResponse(watchlist, 0L);
    }

    @Transactional(readOnly = true)
    public List<WatchlistResponse> getMyWatchlists() {
        User user = getCurrentUser();
        return watchlistRepository.findAllByUserIdOrderByCreatedAtDesc(user.getId())
                .stream()
                .map(w -> toWatchlistResponse(w, watchlistItemRepository.countByWatchlistId(w.getId())))
                .toList();
    }

    @Transactional
    public WatchlistResponse updateWatchlist(Long watchlistId, WatchlistRequest request) {
        User user = getCurrentUser();
        Watchlist watchlist = getOwnedWatchlist(watchlistId, user.getId());

        String cleanName = request.getName().trim();
        if (cleanName.isEmpty()) {
            throw new AppException(ErrorCode.WATCHLIST_NAME_REQUIRED);
        }
        if (!watchlist.getName().equalsIgnoreCase(cleanName)
                && watchlistRepository.existsByUserIdAndNameIgnoreCase(user.getId(), cleanName)) {
            throw new AppException(ErrorCode.WATCHLIST_ALREADY_EXISTS);
        }

        watchlist.setName(cleanName);
        Watchlist saved = watchlistRepository.save(watchlist);
        long count = watchlistItemRepository.countByWatchlistId(saved.getId());
        return toWatchlistResponse(saved, count);
    }

    @Transactional
    public void deleteWatchlist(Long watchlistId) {
        User user = getCurrentUser();
        Watchlist watchlist = getOwnedWatchlist(watchlistId, user.getId());
        watchlistRepository.delete(watchlist);
    }

    @Transactional
    public void addMovieToWatchlist(Long watchlistId, Long movieId) {
        User user = getCurrentUser();
        Watchlist watchlist = getOwnedWatchlist(watchlistId, user.getId());
        addMovieToTargetWatchlist(watchlist, movieId);
    }

    @Transactional
    public void removeMovieFromWatchlist(Long watchlistId, Long movieId) {
        User user = getCurrentUser();
        Watchlist watchlist = getOwnedWatchlist(watchlistId, user.getId());
        removeMovieFromTargetWatchlist(watchlist, movieId);
    }

    @Transactional(readOnly = true)
    public PageResponse<WatchlistItemResponse> getWatchlistItems(Long watchlistId, int page, int size) {
        User user = getCurrentUser();
        Watchlist watchlist = getOwnedWatchlist(watchlistId, user.getId());
        return getPagedItemsForWatchlist(watchlist, page, size);
    }

    @Transactional
    public void addToWatchlist(Long movieId) {
        User user = getCurrentUser();
        Watchlist watchlist = getOrCreateDefaultWatchlist(user);
        addMovieToTargetWatchlist(watchlist, movieId);
    }

    @Transactional
    public void removeFromWatchlist(Long movieId) {
        User user = getCurrentUser();
        Watchlist watchlist = watchlistRepository.findByUserIdAndName(user.getId(), DEFAULT_WATCHLIST_NAME)
                .or(() -> watchlistRepository.findByUserId(user.getId()))
                .orElseThrow(() -> new AppException(ErrorCode.WATCHLIST_NOT_FOUND));
        removeMovieFromTargetWatchlist(watchlist, movieId);
    }

    @Transactional(readOnly = true)
    public WatchlistStatusResponse checkStatus(Long movieId) {
        User user = getCurrentUser();
        var watchlistOpt = watchlistRepository.findByUserIdAndName(user.getId(), DEFAULT_WATCHLIST_NAME)
                .or(() -> watchlistRepository.findByUserId(user.getId()));

        boolean inWatchlist = (watchlistOpt.isPresent() &&
                watchlistItemRepository.existsByWatchlistIdAndMovieId(watchlistOpt.get().getId(), movieId))
                || watchlistItemRepository.existsByWatchlistUserIdAndMovieId(user.getId(), movieId);

        return WatchlistStatusResponse.builder()
                .movieId(movieId)
                .inWatchlist(inWatchlist)
                .build();
    }

    @Transactional(readOnly = true)
    public PageResponse<WatchlistItemResponse> getMyWatchlist(int page, int size) {
        User user = getCurrentUser();
        Watchlist watchlist = getOrCreateDefaultWatchlist(user);
        return getPagedItemsForWatchlist(watchlist, page, size);
    }

    private void addMovieToTargetWatchlist(Watchlist watchlist, Long movieId) {
        if (watchlistItemRepository.existsByWatchlistIdAndMovieId(watchlist.getId(), movieId)) {
            throw new AppException(ErrorCode.MOVIE_ALREADY_IN_WATCHLIST);
        }

        Movie movie = movieRepository.findById(movieId)
                .orElseThrow(() -> new AppException(ErrorCode.MOVIE_NOT_FOUND));

        WatchlistItem item = WatchlistItem.builder()
                .watchlist(watchlist)
                .movie(movie)
                .build();

        watchlistItemRepository.save(item);
    }

    private void removeMovieFromTargetWatchlist(Watchlist watchlist, Long movieId) {
        if (!watchlistItemRepository.existsByWatchlistIdAndMovieId(watchlist.getId(), movieId)) {
            throw new AppException(ErrorCode.MOVIE_NOT_IN_WATCHLIST);
        }
        watchlistItemRepository.deleteByWatchlistIdAndMovieId(watchlist.getId(), movieId);
    }

    private PageResponse<WatchlistItemResponse> getPagedItemsForWatchlist(Watchlist watchlist, int page, int size) {
        int queryPage = Math.max(page - 1, 0);
        Pageable pageable = PageRequest.of(queryPage, size);

        Page<WatchlistItem> itemPage = watchlistItemRepository
                .findByWatchlistIdOrderByCreatedAtDesc(watchlist.getId(), pageable);

        List<WatchlistItemResponse> data = itemPage.getContent().stream()
                .map(item -> WatchlistItemResponse.builder()
                        .id(item.getId())
                        .movie(movieMapper.toMovieSummaryResponse(item.getMovie()))
                        .addedAt(item.getCreatedAt())
                        .build())
                .toList();

        return PageResponse.<WatchlistItemResponse>builder()
                .currentPage(page)
                .pageSize(size)
                .totalPages(itemPage.getTotalPages())
                .totalElements(itemPage.getTotalElements())
                .data(data)
                .build();
    }

    private WatchlistResponse toWatchlistResponse(Watchlist watchlist, long movieCount) {
        return WatchlistResponse.builder()
                .id(watchlist.getId())
                .name(watchlist.getName())
                .movieCount(movieCount)
                .createdAt(watchlist.getCreatedAt())
                .build();
    }
}